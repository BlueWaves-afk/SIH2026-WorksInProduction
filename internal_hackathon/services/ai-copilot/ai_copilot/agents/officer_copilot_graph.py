"""Template-first officer brief builder.

The eventual LangGraph orchestration can call these pure steps. Keeping the
first implementation deterministic makes the demo useful without an LLM and
keeps M7 read-only against M4/M5.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.schemas import AlertCase, ConsentContext, CopilotBrief, RiskEvent, SchemeMatch

from ..explainer.driver_to_sentence import driver_to_sentence
from ..guardrails.citation_validator import validate_scheme_matches
from ..guardrails.output_schema_validator import validate_brief
from .tools.playbook_tool import choose_playbook_action


def _utc(value: datetime) -> datetime:
    """Normalize SQLite's naive UTC values before expiry comparisons."""
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def build_template_brief(
    *,
    event: RiskEvent,
    case: AlertCase,
    consent: ConsentContext,
    scheme_matches: list[SchemeMatch] | None = None,
    locale: str = "en",
) -> CopilotBrief:
    """Build a cited, fixed-playbook brief without calling a model or sending."""

    if _utc(event.expires_at) < datetime.now(UTC):
        raise ValueError("risk event is expired")
    top_drivers = event.top_drivers(3)
    driver_text = [driver_to_sentence(driver, locale) for driver in top_drivers]
    matches = scheme_matches or []
    validate_scheme_matches(matches)
    suggested = choose_playbook_action(band=event.band, drivers=[driver.explanation for driver in top_drivers])
    draft = None
    if consent.may_contact():
        draft = "Namaskar. We noticed a support signal and an officer will contact you to understand the situation. This is not a credit score."
    brief = CopilotBrief(
        case_id=case.case_id,
        summary=f"{event.band.value.title()} support signal for {event.village_id}; officer review is required before any contact.",
        drivers=driver_text,
        scheme_matches=matches,
        suggested_action=suggested.value,
        draft_message=draft,
        citations=[citation for match in matches for citation in match.citations],
        model_version="template-m7-v1",
    )
    return validate_brief(brief)
