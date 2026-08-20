from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditEvent
from .auth import AuthContext


def record_audit(
    db: Session,
    *,
    actor: AuthContext,
    action: str,
    target_id: str,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        actor_id=actor.principal,
        actor_role=actor.role,
        action=action,
        target_id=target_id,
        details=details or {},
        ip_address=ip_address,
    )
    db.add(event)
    return event
