from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.case import AlertCase
from datetime import datetime

router = APIRouter()

@router.post('/{case_id}/acknowledge')
def acknowledge_case(case_id: int, db: Session = Depends(get_db)):
    case = db.query(AlertCase).filter(AlertCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail='Case not found')
    
    case.status = 'Acknowledged'
    case.ack_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    return case

@router.post('/{case_id}/resolve')
def resolve_case(case_id: int, resolution_code: str, notes: str, db: Session = Depends(get_db)):
    case = db.query(AlertCase).filter(AlertCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail='Case not found')
    
    case.status = 'Resolved'
    case.resolution_code = resolution_code
    case.notes = notes
    db.commit()
    db.refresh(case)
    return case

