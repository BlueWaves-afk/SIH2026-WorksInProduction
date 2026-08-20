from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas import farmer as schemas
from app.models import farmer as models

router = APIRouter()

@router.post('/', response_model=schemas.FarmerProfile)
def create_farmer_profile(profile: schemas.FarmerProfileCreate, db: Session = Depends(get_db)):
    db_profile = models.FarmerProfile(**profile.model_dump())
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

