from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from adapters.core.interfaces import ObservationPayload
from app.core.config import settings
from app.core.database import SessionLocal
from app.integrations.live_data import LiveFetchResult
from app.main import app
from app.models.case import AlertCase
from app.models.risk import RiskEvent
from adapters.sources.registry import build_registry


def _profile(token: str = "farmer-integration") -> dict:
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
        "consent_flags": {
            "store_data": True,
            "contact_me": True,
            "use_analytics": True,
            "due_window": True,
        },
    }


def test_flagship_replay_creates_red_case_with_three_drivers_and_safe_stale_path():
    with TestClient(app) as client:
        created = client.post("/api/v1/farmer-profiles", json=_profile())
        assert created.status_code == 201

        replay = client.post(
            "/api/v1/replay/scenario",
            json={"farmer_token": "farmer-integration", "scenario": "rainfall_shock"},
        )
        assert replay.status_code == 200
        event = replay.json()["risk_event"]
        assert event["band"] == "red"
        assert {item["signal"] for item in event["contributors"]} >= {"S1", "S5", "S13"}
        assert all(item["source"] and item["observed_at"] for item in event["contributors"])
        assert replay.json()["case"]["status"] == "new"

        stale = client.post(
            "/api/v1/replay/scenario",
            json={"farmer_token": "farmer-integration", "scenario": "stale_data"},
        )
        stale_event = stale.json()["risk_event"]
        assert stale_event["band"] != "red"
        assert stale_event["confidence"] < 0.45
        assert any("suppressed" in flag for flag in stale_event["context_flags"])
        assert len(client.get("/api/v1/cases").json()["items"]) == 1

        cases = client.get("/api/v1/cases").json()["items"]
        case_id = int(cases[0]["case_id"])
        assert client.post(f"/api/v1/cases/{case_id}/acknowledge").status_code == 200
        assert client.post("/api/v1/copilot/brief", json={"case_id": case_id}).status_code == 200
        resolved = client.post(
            f"/api/v1/cases/{case_id}/resolve",
            json={"resolution_code": "referred", "notes": "FPO referral"},
        )
        assert resolved.status_code == 200
        assert resolved.json()["status"] == "resolved"


def test_farmer_copilot_chat_returns_grounded_template_when_external_provider_is_disabled():
    with TestClient(app) as client:
        created = client.post("/api/v1/farmer-profiles", json=_profile("farmer-chat"))
        assert created.status_code == 201
        replay = client.post("/api/v1/replay/scenario", json={"farmer_token": "farmer-chat", "scenario": "rainfall_shock"})
        assert replay.status_code == 200
        # Replay fixtures are historical by design; make this row current so
        # the chat test exercises the active-event path rather than the stale
        # safety fallback.
        with SessionLocal() as db:
            row = db.query(RiskEvent).filter(RiskEvent.farmer_token == "farmer-chat").order_by(RiskEvent.id.desc()).first()
            assert row is not None
            row.expires_at = datetime.utcnow() + timedelta(hours=1)
            db.commit()

        response = client.post(
            "/api/v1/copilot/chat",
            json={"farmer_token": "farmer-chat", "message": "Why is my status red?", "locale": "en"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["provider"] == "template"
        assert body["safe_fallback"] is True
        assert body["event_id"]
        assert body["citations"]
        assert "credit" in body["disclaimer"].lower()


def test_error_envelope_and_consent_withdrawal_are_enforced():
    with TestClient(app) as client:
        assert client.get("/api/v1/not-a-route").json()["code"] == "not_found"
        created = client.post("/api/v1/farmer-profiles", json=_profile("farmer-consent"))
        assert created.status_code == 201
        token = created.json()["farmer_token"]
        withdrawn = client.put(f"/api/v1/consents/{token}", json={"storage": False, "contact": False})
        assert withdrawn.status_code == 200
        assert withdrawn.json()["consent"]["store_data"] is False
        observation = client.post("/api/v1/observations", json={"farmer_token": token, "source": "imd", "observed_at": "2026-06-01T00:00:00Z", "metric": "rainfall_deviation_pct", "value": -10, "ttl_seconds": 3600})
        assert observation.status_code == 403


def test_profile_bootstraps_a_conservative_initial_status():
    token = "farmer-initial-status"
    with TestClient(app) as client:
        created = client.post("/api/v1/farmer-profiles", json=_profile(token))
        assert created.status_code == 201

        events = client.get(f"/api/v1/risk-events?farmer_token={token}")
        assert events.status_code == 200
        items = events.json()["items"]
        assert len(items) == 1
        assert items[0]["band"] == "green"
        assert items[0]["confidence"] == 0
        assert "escalation suppressed: low confidence" in items[0]["context_flags"]


def test_repeating_authenticated_farmer_setup_reuses_existing_profile():
    headers = {"x-demo-role": "farmer", "x-demo-principal": "repeat-onboarding-user"}
    with TestClient(app) as client:
        first = client.post("/api/v1/farmer-profiles", json=_profile("first-token"), headers=headers)
        assert first.status_code == 201

        repeated = client.post("/api/v1/farmer-profiles", json=_profile("second-token"), headers=headers)
        assert repeated.status_code == 200
        assert repeated.json()["farmer_token"] == first.json()["farmer_token"]


def test_farmer_token_is_not_a_bearer_credential():
    owner_headers = {"x-demo-role": "farmer", "x-demo-principal": "supabase-user-owner"}
    stranger_headers = {"x-demo-role": "farmer", "x-demo-principal": "supabase-user-stranger"}
    with TestClient(app) as client:
        created = client.post(
            "/api/v1/farmer-profiles",
            json=_profile("opaque-farmer-resource"),
            headers=owner_headers,
        )
        assert created.status_code == 201
        assert client.get("/api/v1/farmer-profiles/me", headers=owner_headers).json()["farmer_token"] == "opaque-farmer-resource"

        # Knowing the opaque token does not authorize consent, observations,
        # risk reads, exports, or deletion for another Supabase subject.
        assert client.get("/api/v1/consents/opaque-farmer-resource", headers=stranger_headers).status_code == 403
        assert client.get("/api/v1/consents/opaque-farmer-resource/export", headers=stranger_headers).status_code == 403
        assert client.delete("/api/v1/consents/opaque-farmer-resource", headers=stranger_headers).status_code == 403
        observation = {
            "farmer_token": "opaque-farmer-resource",
            "source": "farmer_report",
            "observed_at": "2026-06-01T00:00:00Z",
            "metric": "acute_farmer_report",
            "value": "crop damage",
            "ttl_seconds": 3600,
        }
        assert client.post("/api/v1/observations", json=observation, headers=stranger_headers).status_code == 403
        assert client.get(
            "/api/v1/risk-events?farmer_token=opaque-farmer-resource",
            headers=stranger_headers,
        ).status_code == 403


def test_officer_cannot_override_jwt_district_scope():
    headers = {
        "x-demo-role": "extension_officer",
        "x-demo-principal": "officer-nashik",
        "x-demo-district": "nashik",
    }
    with TestClient(app) as client:
        assert client.get("/api/v1/cases?district_id=pune", headers=headers).status_code == 403
        assert client.get("/api/v1/risk-events?district_id=pune", headers=headers).status_code == 403
        assert client.get("/api/v1/analytics/district?district_id=pune", headers=headers).status_code == 403


def test_live_recalculate_persists_provider_observations_before_scoring(monkeypatch):
    now = datetime(2026, 8, 7, tzinfo=UTC)
    live_rows = [
        ObservationPayload(
            source="imd",
            observed_at=now,
            metric="rainfall_deviation_pct",
            value=-35,
            unit="percent",
            ttl=timedelta(days=2),
        ),
        ObservationPayload(
            source="agmarknet",
            observed_at=now,
            metric="mandi_price_deviation_pct",
            value={"deviation_pct": -25, "below_msp": True},
            unit="percent",
            ttl=timedelta(days=3),
        ),
    ]

    def fake_fetch_live(**_kwargs):
        return LiveFetchResult(
            observations=live_rows,
            sources=[
                {"source": "imd", "mode": "real", "configured": True, "observation_count": 1, "health": {}},
                {"source": "agmarknet", "mode": "real", "configured": True, "observation_count": 1, "health": {}},
            ],
            errors=[],
        )

    monkeypatch.setattr("app.integrations.live_data.fetch_live", fake_fetch_live)
    monkeypatch.setattr(settings, "live_data_enabled", True)
    with TestClient(app) as client:
        created = client.post("/api/v1/farmer-profiles", json=_profile("farmer-live"))
        assert created.status_code == 201
        response = client.post(
            "/api/v1/risk-events/recalculate",
            json={"farmer_token": "farmer-live", "source_mode": "live", "as_of": now.isoformat()},
        )
        assert response.status_code == 201
        event = response.json()
        assert {item["source"] for item in event["contributors"]} >= {"IMD", "agmarknet"}


def test_recalculation_projects_one_open_case_and_cohort_analytics_is_suppressed():
    with TestClient(app) as client:
        token = "farmer-projection"
        assert client.post("/api/v1/farmer-profiles", json=_profile(token)).status_code == 201
        replay = client.post("/api/v1/replay/scenario", json={"farmer_token": token, "scenario": "rainfall_shock"})
        assert replay.status_code == 200
        first_case_id = str(replay.json()["case"]["case_id"])
        recalculated = client.post("/api/v1/risk-events/recalculate", json={"farmer_token": token})
        assert recalculated.status_code == 201
        cases = client.get("/api/v1/cases").json()["items"]
        assert [item["case_id"] for item in cases].count(first_case_id) == 1
        analytics = client.get("/api/v1/analytics/district")
        assert analytics.status_code == 200
        assert analytics.json()["suppressed"] is True


def test_observation_boundary_rejects_sensitive_and_malformed_values():
    with TestClient(app) as client:
        assert client.post("/api/v1/farmer-profiles", json=_profile("farmer-validation")).status_code == 201
        banned = client.post(
            "/api/v1/observations",
            json={"farmer_token": "farmer-validation", "source": "farmer_report", "observed_at": "2026-06-01T00:00:00Z", "metric": "credit_score", "value": 10},
        )
        assert banned.status_code == 422
        malformed = client.post(
            "/api/v1/observations",
            json={"farmer_token": "farmer-validation", "source": "imd", "observed_at": "2026-06-01T00:00:00Z", "metric": "rainfall_deviation_pct", "value": 9999},
        )
        assert malformed.status_code == 422


def test_all_canonical_sources_are_registered_without_credentials():
    registry = build_registry({})
    expected = {"imd", "agmarknet", "agristack", "bhashini", "bhuvan", "msp", "sentinel2", "soil"}
    assert set(registry.sources()) == expected


def test_sla_scanner_persists_breach_and_queue_exposes_it():
    token = "farmer-sla"
    with TestClient(app) as client:
        assert client.post("/api/v1/farmer-profiles", json=_profile(token)).status_code == 201
        replay = client.post("/api/v1/replay/scenario", json={"farmer_token": token, "scenario": "rainfall_shock"})
        assert replay.status_code == 200
        with SessionLocal() as db:
            case = db.query(AlertCase).filter(AlertCase.farmer_token == token).first()
            assert case is not None
            case.sla_due_at = datetime.utcnow() - timedelta(minutes=1)
            db.commit()
        scan = client.post("/api/v1/cases/sla/scan")
        assert scan.status_code == 200
        assert scan.json()["breached"] == 1
        listed = client.get("/api/v1/cases").json()["items"]
        assert any(item["farmer_token"] == token and item["sla_breached"] is True for item in listed)
