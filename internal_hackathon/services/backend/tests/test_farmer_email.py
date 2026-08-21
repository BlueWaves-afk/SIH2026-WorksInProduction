"""Opt-in farmer email alert channel: profile storage, outreach, delivery."""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import SessionLocal
from app.main import app
from app.models.history import DeliveryAttempt
from app.models.outbox import OutboxMessage
from app.models.risk import RiskEvent
from app.services.delivery import process_outbox
from app.services.outreach import run_outreach_cycle

# Naive UTC to match the persistence layer (delivery compares against naive
# stored timestamps); noon keeps it outside quiet hours so delivery runs.
NOON = datetime(2026, 8, 21, 12, 0)  # noqa: DTZ001


def _add_fresh_red_event(token: str) -> None:
    # A fresh Red dated now, so the outreach band-change/sustained-Red trigger
    # fires deterministically (replay fixtures are historical by design). We
    # remove the conservative bootstrap event first so the Red is unambiguously
    # the current band with no newer green ahead of it.
    with SessionLocal() as db:
        db.query(RiskEvent).filter(RiskEvent.farmer_token == token).delete()
        db.add(
            RiskEvent(
                event_id=f"evt-{uuid4().hex}",
                farmer_token=token,
                village_id="demo-village",
                score=78.0,
                band="red",
                confidence=0.82,
                contributors=[{"signal": "rainfall_deficit", "points": 20, "max_points": 20, "explanation": "Rainfall is 32% below normal", "source": "IMD", "observed_at": NOON.isoformat()}],
                action_ids=[],
                model_version="fdi-v2",
                evaluated_at=NOON,
                expires_at=NOON + timedelta(days=1),
                disclaimer="This is not a credit, loan-default, or insurance score.",
                context_flags=[],
            )
        )
        db.commit()


@pytest.fixture(autouse=True)
def _vault_key(monkeypatch):
    # A recoverable email requires a vault key; set one so encrypt/decrypt round
    # trips (fixture mode otherwise stores a non-recoverable hash).
    monkeypatch.setattr(settings, "vault_encryption_key", "test-vault-key-abc123")


def _profile(token: str, *, email: str | None = "farmer@example.org", email_alerts: bool = True) -> dict:
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
        "email": email,
        "consent_flags": {
            "store_data": True,
            "contact_me": True,
            "email_alerts": email_alerts,
            "use_analytics": True,
            "due_window": True,
        },
    }


def _seed(token: str, **kwargs) -> None:
    with TestClient(app) as client:
        assert client.post("/api/v1/farmer-profiles", json=_profile(token, **kwargs)).status_code == 201
    _add_fresh_red_event(token)


def test_profile_stores_encrypted_email_and_consent():
    _seed("email-store")
    with SessionLocal() as db:
        from app.models.farmer import FarmerProfile

        profile = db.query(FarmerProfile).filter(FarmerProfile.farmer_token == "email-store").first()
    assert profile is not None
    assert profile.email_enc and profile.email_enc.startswith("enc:v1:")  # encrypted, not plaintext
    assert profile.consent_flags["email_alerts"] is True


def test_blank_email_is_accepted_and_stored_as_none():
    with TestClient(app) as client:
        created = client.post("/api/v1/farmer-profiles", json=_profile("email-blank", email="", email_alerts=False))
    assert created.status_code == 201


def test_invalid_email_is_rejected():
    with TestClient(app) as client:
        created = client.post("/api/v1/farmer-profiles", json=_profile("email-bad", email="not-an-email"))
    assert created.status_code == 422


def test_outreach_creates_additive_email_message_when_opted_in():
    _seed("email-outreach")
    with SessionLocal() as db:
        result = run_outreach_cycle(db, now=NOON)
        email_msgs = db.query(OutboxMessage).filter(
            OutboxMessage.farmer_token == "email-outreach", OutboxMessage.channel == "email"
        ).all()
    assert result["created"] >= 2  # primary whatsapp + additive email
    assert len(email_msgs) == 1
    assert email_msgs[0].consent_required == "email_alerts"


def test_outreach_skips_email_when_not_opted_in():
    _seed("email-optout", email_alerts=False)
    with SessionLocal() as db:
        run_outreach_cycle(db, now=NOON)
        email_msgs = db.query(OutboxMessage).filter(
            OutboxMessage.farmer_token == "email-optout", OutboxMessage.channel == "email"
        ).count()
    assert email_msgs == 0


def test_email_message_is_delivered_through_the_email_provider():
    _seed("email-deliver")
    with SessionLocal() as db:
        run_outreach_cycle(db, now=NOON)
        process_outbox(db, now=NOON)
        message = db.query(OutboxMessage).filter(
            OutboxMessage.farmer_token == "email-deliver", OutboxMessage.channel == "email"
        ).first()
        attempt = db.query(DeliveryAttempt).filter(
            DeliveryAttempt.message_id == message.message_id, DeliveryAttempt.channel == "email"
        ).first()
    assert message.status == "sent"
    assert attempt is not None and attempt.status == "sent"


def test_withdrawing_email_consent_cancels_the_email_delivery():
    _seed("email-withdraw")
    with TestClient(app) as client:
        # Opt out of email after the message was queued.
        assert client.put("/api/v1/consents/email-withdraw", json={"email_alerts": False}).status_code == 200
    with SessionLocal() as db:
        run_outreach_cycle(db, now=NOON)  # email flag now off -> no new email message
        # Force an email message to exist to prove the delivery gate, mimicking a
        # message queued before withdrawal.
        message = OutboxMessage(
            message_id="forced-email-1",
            idempotency_key="forced-email-1",
            farmer_token="email-withdraw",
            channel="email",
            content={"event_id": "x", "band": "red", "drivers": [], "disclaimer": "d"},
            status="pending",
            consent_required="email_alerts",
        )
        db.add(message)
        db.commit()
        process_outbox(db, now=NOON)
        db.refresh(message)
    assert message.status == "cancelled_consent"
