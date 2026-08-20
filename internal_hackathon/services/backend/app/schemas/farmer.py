from pydantic import BaseModel, Field
from datetime import date
from typing import Optional

class ConsentFlags(BaseModel):
    store_data: bool = False
    contact_me: bool = False
    use_analytics: bool = False

class FarmerProfileCreate(BaseModel):
    farmer_token: str
    village_id: str
    locale: str = Field(..., description='hi or mr')
    crop: str
    sowing_date: date
    irrigation_type: str = Field(..., description='rainfed or irrigated')
    area_band: str = Field(..., description='<1, 1-2, or >2 ha')
    phone_enc: str
    consent_flags: ConsentFlags

class FarmerProfile(FarmerProfileCreate):
    id: int

    class Config:
        from_attributes = True

