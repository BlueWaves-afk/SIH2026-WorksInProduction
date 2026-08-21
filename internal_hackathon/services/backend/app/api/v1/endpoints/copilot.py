from __future__ import annotations

import base64
import binascii
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.api.v1.endpoints.cases import _case_response
from app.api.v1.endpoints.risk_events import event_response
from app.core.config import settings
from app.core.database import get_db
from app.integrations.copilot import template_brief_builder
from app.integrations.sarvam import SarvamSpeechProviderError, build_sarvam_speech_provider
from app.models.case import AlertCase
from app.models.farmer import FarmerProfile
from app.models.risk import RiskEvent
from app.schemas import (
    Citation,
    ConsentContext,
    CopilotBrief,
    CopilotBriefRequest,
    CopilotConversationRequest,
    CopilotConversationResponse,
    CopilotSpeechSynthesizeRequest,
    CopilotSpeechTranscribeRequest,
    CopilotSpeechTranscribeResponse,
    SchemeMatch,
)
from app.security import AuthContext, authorize_farmer_profile, require_roles
from app.security.audit import record_audit
from app.services.copilot_conversation import answer_farmer_message
from app.services.scoring import BOOTSTRAP_EVENT_FLAG

router = APIRouter()


def _build_brief(event_row: RiskEvent, case_row: AlertCase, profile: FarmerProfile | None, locale: str) -> CopilotBrief:
    event = event_response(event_row)
    case = _case_response(case_row)
    flags = profile.consent_flags if profile else {}
    consent = ConsentContext(
        farmer_token=case.farmer_token,
        storage=bool(flags.get("store_data", flags.get("storage", False))),
        contact=bool(flags.get("contact_me", flags.get("contact", False))),
        analytics=bool(flags.get("use_analytics", flags.get("analytics", False))),
        due_window=bool(flags.get("due_window", False)),
    )
    matches: list[SchemeMatch] = []
    for index, scheme in enumerate((profile.schemes_enrolled if profile else []) or []):
        matches.append(
            SchemeMatch(
                scheme=scheme,
                why="The farmer profile records this scheme; an officer must confirm current eligibility.",
                citations=[Citation(source_doc="farmer-profile-consent", chunk_id=f"scheme-{index}", quote=f"Profile scheme: {scheme}")],
                verified=False,
            )
        )
    try:
        build_template_brief = template_brief_builder()
        return build_template_brief(event=event, case=case, consent=consent, scheme_matches=matches, locale=locale)
    except (ModuleNotFoundError, ValueError) as exc:
        drivers = [f"Key signal: {driver.explanation}." for driver in event.top_drivers()]
        return CopilotBrief(
            case_id=case.case_id,
            summary=(
                f"{event.band.value.title()} support signal for {event.village_id}; officer review is required."
                if not isinstance(exc, ValueError)
                else f"This risk event is no longer current for {event.village_id}; refresh it before taking action."
            ),
            drivers=drivers,
            scheme_matches=matches,
            suggested_action=("SCHEDULE_VISIT" if event.band.value == "red" else "SEND_ADVISORY") if not isinstance(exc, ValueError) else "RECALCULATE_RISK_EVENT",
            draft_message=("Namaskar. An officer will contact you to understand the situation. This is not a credit score." if consent.may_contact() and not isinstance(exc, ValueError) else None),
            citations=[citation for match in matches for citation in match.citations],
            model_version="template-m7-v1" if not isinstance(exc, ValueError) else "template-m7-expired",
        )


@router.post("/brief", response_model=CopilotBrief)
def copilot_brief(
    payload: CopilotBriefRequest,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("extension_officer", "district_admin", "admin", "auditor")),
):
    case = db.query(AlertCase).filter(AlertCase.id == payload.case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    event = db.query(RiskEvent).filter(RiskEvent.event_id == case.event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Risk event not found")
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == case.farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    if profile and not bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False))):
        raise HTTPException(status_code=403, detail="Storage consent is required for copilot context")
    brief = _build_brief(event, case, profile, payload.locale)
    record_audit(db, actor=actor, action="copilot.brief", target_id=str(case.id), details={"model_version": brief.model_version, "draft": bool(brief.draft_message)})
    db.commit()
    return brief


@router.post("/chat", response_model=CopilotConversationResponse)
def copilot_chat(
    payload: CopilotConversationRequest,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin", "auditor")),
):
    """Answer a bounded farmer question from the current deterministic event.

    This route never sends a notification or mutates a score/case.  Sarvam is
    optional; when disabled, unavailable, or unsafe, the template answer is
    returned with ``safe_fallback=true``.
    """

    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == payload.farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    authorize_farmer_profile(actor, profile)
    if not bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False))):
        raise HTTPException(status_code=403, detail="Storage consent is required for copilot context")

    # A stale score is never narrated.  If there is no active event, the agent
    # receives an explicit empty context and must tell the farmer to refresh.
    event_rows = (
        db.query(RiskEvent)
        .filter(RiskEvent.farmer_token == payload.farmer_token, RiskEvent.expires_at >= datetime.utcnow())
        .order_by(RiskEvent.evaluated_at.desc(), RiskEvent.id.desc())
        .all()
    )
    scored_events = [row for row in event_rows if BOOTSTRAP_EVENT_FLAG not in (row.context_flags or [])]
    event_row = (scored_events or event_rows or [None])[0]
    event = event_response(event_row) if event_row else None
    answer = answer_farmer_message(
        settings=settings,
        profile=profile,
        event=event,
        message=payload.message,
        history=payload.history,
        locale=payload.locale,
    )
    record_audit(
        db,
        actor=actor,
        action="copilot.chat",
        target_id=payload.farmer_token,
        details={
            "provider": answer.provider,
            "model": answer.model,
            "safe_fallback": answer.safe_fallback,
            "event_id": answer.event_id,
            "locale": payload.locale,
        },
    )
    db.commit()
    return CopilotConversationResponse(
        reply=answer.reply,
        provider=answer.provider,
        model=answer.model,
        safe_fallback=answer.safe_fallback,
        citations=answer.citations,
        event_id=answer.event_id,
    )


def _speech_profile(payload_farmer_token: str, db: Session, actor: AuthContext) -> FarmerProfile:
    profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == payload_farmer_token).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    authorize_farmer_profile(actor, profile)
    if not bool((profile.consent_flags or {}).get("store_data", (profile.consent_flags or {}).get("storage", False))):
        raise HTTPException(status_code=403, detail="Storage consent is required for speech support")
    return profile


@router.post("/speech/transcribe", response_model=CopilotSpeechTranscribeResponse)
def copilot_speech_transcribe(
    payload: CopilotSpeechTranscribeRequest,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin", "auditor")),
):
    """Transcribe a short, non-persisted farmer audio clip through Sarvam."""

    _speech_profile(payload.farmer_token, db, actor)
    audio = _decode_audio(payload.audio_base64)
    mime_type = _audio_mime_type(payload.audio_mime_type)
    provider = build_sarvam_speech_provider(settings)
    try:
        result = provider.transcribe(audio, language_code=payload.language_code, mime_type=mime_type)
    except SarvamSpeechProviderError as exc:
        raise HTTPException(status_code=503, detail="Speech transcription is temporarily unavailable") from exc
    record_audit(
        db,
        actor=actor,
        action="copilot.speech.transcribe",
        target_id=payload.farmer_token,
        details={"provider": "sarvam", "language_code": result.language},
    )
    db.commit()
    return CopilotSpeechTranscribeResponse(
        text=result.text,
        language_code=result.language,
        confidence=result.confidence,
    )


@router.post("/speech/synthesize")
def copilot_speech_synthesize(
    payload: CopilotSpeechSynthesizeRequest,
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("farmer", "extension_officer", "district_admin", "admin", "auditor")),
):
    """Render approved/grounded text to audio through Sarvam TTS."""

    _speech_profile(payload.farmer_token, db, actor)
    provider = build_sarvam_speech_provider(settings)
    try:
        audio = provider.synthesize(payload.text, language_code=payload.language_code)
    except SarvamSpeechProviderError as exc:
        raise HTTPException(status_code=503, detail="Speech synthesis is temporarily unavailable") from exc
    record_audit(
        db,
        actor=actor,
        action="copilot.speech.synthesize",
        target_id=payload.farmer_token,
        details={"provider": "sarvam", "language_code": payload.language_code},
    )
    db.commit()
    return Response(content=audio, media_type="audio/wav", headers={"cache-control": "no-store", "x-provider": "sarvam"})


def _decode_audio(value: str) -> bytes:
    encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
    try:
        audio = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(status_code=422, detail="audio_base64 is invalid") from exc
    if not audio or len(audio) > 6_000_000:
        raise HTTPException(status_code=422, detail="audio payload must be between 1 byte and 6 MB")
    return audio


def _audio_mime_type(value: str) -> str:
    """Allow only browser audio containers accepted by the speech provider."""

    normalized = value.split(";", 1)[0].strip().lower()
    allowed = {"audio/wav", "audio/x-wav", "audio/webm", "audio/ogg", "audio/mp4", "audio/mpeg"}
    if normalized not in allowed:
        raise HTTPException(status_code=422, detail="audio_mime_type is unsupported")
    return normalized
