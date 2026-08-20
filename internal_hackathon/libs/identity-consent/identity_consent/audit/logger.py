"""Framework-neutral audit event shape."""

from datetime import UTC, datetime
from typing import Any


def write_audit_event(*, actor_id: str, actor_role: str, action: str, target_id: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"actor_id": actor_id, "actor_role": actor_role, "action": action, "target_id": target_id, "details": details or {}, "timestamp": datetime.now(UTC).isoformat()}
