"""Case SLA breach projection.

Breaching a target changes queue priority and creates an audit trail; it never
silently changes case ownership or status.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.case import AlertCase
from app.security import AuthContext
from app.security.audit import record_audit


def scan_sla_breaches(db: Session, *, now: datetime | None = None, actor: AuthContext | None = None) -> dict[str, int | str]:
    now = now or datetime.utcnow()
    actor = actor or AuthContext(principal="sla-scanner", role="admin", scopes=frozenset({"*"}))
    rows = (
        db.query(AlertCase)
        .filter(
            AlertCase.status.in_(["new", "acknowledged", "visited", "referred"]),
            AlertCase.sla_due_at.isnot(None),
            AlertCase.sla_due_at < now,
            (AlertCase.sla_breached.is_(None) | (AlertCase.sla_breached != "true")),
        )
        .all()
    )
    for case in rows:
        case.sla_breached = "true"
        case.sla_breached_at = now
        record_audit(db, actor=actor, action="case.sla_breach", target_id=str(case.id), details={"sla_due_at": case.sla_due_at.isoformat() if case.sla_due_at else None})
    db.commit()
    return {"breached": len(rows), "scanned_at": now.isoformat()}


__all__ = ["scan_sla_breaches"]
