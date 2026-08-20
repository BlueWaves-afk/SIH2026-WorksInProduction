"""Scheduled data-minimisation jobs; audit records are intentionally retained."""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.observation import Observation
from app.models.outbox import OutboxMessage


def run_retention_cycle(db: Session, *, now: datetime | None = None) -> dict[str, int]:
    now = now or datetime.utcnow()
    observation_cutoff = now - timedelta(days=settings.observation_retention_days)
    outbox_cutoff = now - timedelta(days=settings.outbox_retention_days)
    observations = db.query(Observation).filter(Observation.created_at < observation_cutoff).delete(synchronize_session=False)
    outbox = db.query(OutboxMessage).filter(OutboxMessage.created_at < outbox_cutoff, OutboxMessage.status.in_(["sent", "cancelled_consent", "dead_letter"])).delete(synchronize_session=False)
    db.commit()
    return {"observations_deleted": observations, "outbox_deleted": outbox, "audit_deleted": 0}
