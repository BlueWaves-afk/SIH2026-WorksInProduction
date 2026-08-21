"""End-to-end coverage for the automatic live loop: scheduled ingestion,
officer email digest, and Sarvam speech health/error reporting."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from adapters.core.interfaces import ObservationPayload
from app.core.config import settings
from app.core.database import SessionLocal
from app.integrations.email import BaseEmailProvider, EmailResult
from app.integrations.live_data import LiveFetchResult, sync_profile_observations
from app.main import app
from app.models.farmer import FarmerProfile
from app.services.digest import build_district_digest, send_district_digests
from app.services.ingestion import run_ingestion_cycle


def _profile(token: str) -> dict:
    return {
        "farmer_token": token,
        "village_id": "demo-village",
        "locale": "en",
        "crop": "cotton",
        "sowing_date": "2026-04-20",
        "irrigation_type": "rainfed",
        "area_band": "<1",
        "institutional_access": "limited",
        "soil_retention": "poor",
        "schemes_enrolled": ["PMFBY"],
        "consent_flags": {"store_data": True, "contact_me": True, "use_analytics": True, "due_window": True},
    }


class _CapturingEmailProvider(BaseEmailProvider):
    provider = "capture"

    def __init__(self) -> None:
        self.sent: list[dict] = []

    @property
    def configured(self) -> bool:
        return True

    def send(self, *, to, subject, text, html=None):
        self.sent.append({"to": to, "subject": subject, "text": text, "html": html})
        return EmailResult(provider=self.provider, accepted=list(to))


def _seed_red_farmer(token: str) -> None:
    with TestClient(app) as client:
        assert client.post("/api/v1/farmer-profiles", json=_profile(token)).status_code == 201
        replay = client.post("/api/v1/replay/scenario", json={"farmer_token": token, "scenario": "rainfall_shock"})
        assert replay.status_code == 200


def test_ingestion_cycle_rescores_the_cohort_without_live_fetch():
    _seed_red_farmer("farmer-ingest")
    with SessionLocal() as db:
        # live=False rescores stored observations — no network, deterministic.
        summary = run_ingestion_cycle(db, live=False)
    assert summary["rescored"] >= 1
    assert summary["live_fetched"] == 0
    assert summary["failed"] == 0
    assert summary["bands"]["red"] + summary["bands"]["amber"] + summary["bands"]["green"] == summary["rescored"]


def test_ingestion_cycle_counts_live_fetch_when_source_succeeds(monkeypatch):
    # A live source is only fetched when its adapter is in `real` mode with
    # credentials; here we stand in for a working source to prove the happy
    # path increments live_fetched (the network call itself is out of scope).
    _seed_red_farmer("farmer-livefetch")
    calls: list[str] = []
    monkeypatch.setattr(
        "app.services.ingestion.sync_profile_observations",
        lambda db, profile, as_of=None: calls.append(profile.farmer_token) or ([], None),
    )
    with SessionLocal() as db:
        summary = run_ingestion_cycle(db, live=True)
    assert calls  # the source was consulted
    assert summary["live_fetched"] >= 1
    assert summary["failed"] == 0


def test_partial_live_refresh_keeps_successful_source_rows(monkeypatch):
    token = "farmer-partial-live"
    _seed_red_farmer(token)
    observed_at = datetime.now(UTC)
    monkeypatch.setattr(
        "app.integrations.live_data.fetch_live",
        lambda **_: LiveFetchResult(
            observations=[
                ObservationPayload(
                    source="agmarknet",
                    observed_at=observed_at,
                    village_id="demo-village",
                    metric="mandi_price_deviation_pct",
                    value={"deviation_pct": -18, "below_msp": True},
                    unit="percent",
                    ttl=timedelta(days=3),
                )
            ],
            sources=[],
            errors=[{"source": "sentinel2", "message": "provider unavailable"}],
        ),
    )
    with SessionLocal() as db:
        profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == token).first()
        assert profile is not None
        rows, result = sync_profile_observations(db, profile)
        db.commit()
    assert result.errors
    assert [row.metric for row in rows] == ["mandi_price_deviation_pct"]


def test_ingestion_cycle_skips_profiles_without_storage_consent():
    token = "farmer-noconsent"
    with TestClient(app) as client:
        profile = _profile(token)
        profile["consent_flags"] = {"store_data": False, "contact_me": False}
        assert client.post("/api/v1/farmer-profiles", json=profile).status_code == 201
    with SessionLocal() as db:
        summary = run_ingestion_cycle(db, live=False)
    assert summary["skipped_no_consent"] >= 1


def test_district_digest_builds_and_sends_officer_summary(monkeypatch):
    _seed_red_farmer("farmer-digest")
    monkeypatch.setattr(settings, "district_digest_recipients", "ops@example.org, lead@example.org")
    provider = _CapturingEmailProvider()
    with SessionLocal() as db:
        summary = build_district_digest(db)
        result = send_district_digests(db, provider=provider)

    assert summary["totals"]["open"] >= 1
    assert result["sent"] is True
    assert result["recipients"] == 2
    assert len(provider.sent) == 1
    message = provider.sent[0]
    assert message["to"] == ["ops@example.org", "lead@example.org"]
    assert "officer digest" in message["subject"].lower()
    # Identity-light: never leak the farmer token in an officer email.
    assert "farmer-digest" not in message["text"]


def test_district_digest_no_recipients_is_a_safe_noop(monkeypatch):
    monkeypatch.setattr(settings, "district_digest_recipients", "")
    with SessionLocal() as db:
        result = send_district_digests(db)
    assert result["sent"] is False
    assert result["reason"] == "no_recipients"


def test_speech_health_reports_unconfigured_in_test_env(monkeypatch):
    # The developer worktree may contain a real Sarvam key for smoke tests;
    # this test is specifically the missing-provider branch and must isolate
    # that environment-dependent setting.
    monkeypatch.setattr(settings, "sarvam_api_key", None)
    with TestClient(app) as client:
        created = client.post("/api/v1/farmer-profiles", json=_profile("farmer-voice-health"))
        assert created.status_code == 201
        health = client.get("/api/v1/copilot/speech/health")
    assert health.status_code == 200
    body = health.json()
    assert body["configured"] is False  # no SARVAM_API_KEY in the test environment
    assert body["provider"] == "sarvam"
    assert body["stt_model"] and body["tts_model"]


def test_speech_synthesize_returns_specific_not_configured_error(monkeypatch):
    monkeypatch.setattr(settings, "sarvam_api_key", None)
    token = "farmer-voice-tts"
    with TestClient(app) as client:
        assert client.post("/api/v1/farmer-profiles", json=_profile(token)).status_code == 201
        response = client.post(
            "/api/v1/copilot/speech/synthesize",
            json={"farmer_token": token, "text": "Your cotton needs attention.", "language_code": "en-IN"},
        )
    assert response.status_code == 503
    assert response.headers.get("x-speech-status") == "not_configured"
    # The app wraps HTTPException.detail into an error envelope under "message".
    assert "not configured" in response.json()["message"].lower()
