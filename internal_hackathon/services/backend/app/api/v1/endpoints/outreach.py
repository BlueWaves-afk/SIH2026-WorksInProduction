from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.security import AuthContext, require_roles
from app.services.outreach import run_outreach_cycle

router = APIRouter()


@router.post("/cycle")
def outreach_cycle(
    db: Session = Depends(get_db),
    actor: AuthContext = Depends(require_roles("district_admin", "admin")),
):
    return run_outreach_cycle(db, actor=actor)
