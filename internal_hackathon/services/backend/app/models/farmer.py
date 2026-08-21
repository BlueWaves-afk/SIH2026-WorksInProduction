from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, JSON, String
from app.core.database import Base

class FarmerProfile(Base):
    __tablename__ = 'farmer_profiles'

    id = Column(Integer, primary_key=True, index=True)
    farmer_token = Column(String, unique=True, index=True)
    # Supabase ``sub`` that owns this opaque resource token.  The token is an
    # identifier only; it is never accepted as proof of identity.
    auth_subject = Column(String, unique=True, index=True, nullable=True)
    village_id = Column(String, index=True)
    locale = Column(String)
    crop = Column(String)
    sowing_date = Column(Date)
    irrigation_type = Column(String)
    area_band = Column(String)
    phone_enc = Column(String)
    email_enc = Column(String, nullable=True)
    consent_flags = Column(JSON)
    secondary_crop = Column(String, nullable=True)
    schemes_enrolled = Column(JSON, default=list)
    institutional_access = Column(String, default="unknown")
    soil_retention = Column(String, default="unknown")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
