from sqlalchemy import Column, Integer, String, Date, Boolean, JSON
from app.core.database import Base

class FarmerProfile(Base):
    __tablename__ = 'farmer_profiles'

    id = Column(Integer, primary_key=True, index=True)
    farmer_token = Column(String, unique=True, index=True)
    village_id = Column(String, index=True)
    locale = Column(String)
    crop = Column(String)
    sowing_date = Column(Date)
    irrigation_type = Column(String)
    area_band = Column(String)
    phone_enc = Column(String)
    consent_flags = Column(JSON)

