from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Language(str, Enum):
    hi = "hi"
    mr = "mr"

class IrrigationType(str, Enum):
    rainfed = "rainfed"
    irrigated = "irrigated"

class AreaBand(str, Enum):
    lt_1 = "<1"
    one_to_two = "1-2"
    gt_2 = ">2"

class RiskBand(str, Enum):
    green = "green"
    amber = "amber"
    red = "red"

class DataQuality(str, Enum):
    fresh = "fresh"
    stale = "stale"
    missing = "missing"

class CaseStatus(str, Enum):
    new = "new"
    acknowledged = "acknowledged"
    visited = "visited"
    referred = "referred"
    resolved = "resolved"

class ConsentFlags(BaseModel):
    store_data: bool = False
    allow_contact: bool = False
    allow_analytics: bool = False


class FarmerProfileBase(BaseModel):
    village_id: str
    locale: Language
    crop: str
    sowing_date: date
    irrigation_type: IrrigationType
    area_band: AreaBand
    phone: str  
    consent_flags: ConsentFlags

class FarmerProfileCreate(FarmerProfileBase):
    pass

class FarmerProfile(FarmerProfileBase):
    farmer_token: str
    created_at: datetime

    class Config:
        from_attributes = True


class Observation(BaseModel):
    source: str  
    observed_at: datetime
    village_id: Optional[str] = None
    plot_grid: Optional[str] = None
    metric: str
    value: float
    unit: str
    quality: DataQuality
    ttl_hours: int


class MarketQuote(BaseModel):
    commodity: str
    mandi_id: str
    date: date
    modal_price: float
    arrivals: Optional[float] = None
    source: str
    quality: DataQuality


class DueWindow(BaseModel):
    farmer_token: str
    due_date_band: str   # coarse band, e.g. "0-15d"
    amount_band: str     # coarse band, e.g. "5k-10k"
    consent: bool


class RiskEventContributor(BaseModel):
    driver: str          # e.g. "rainfall_shock"
    detail: str          # human-readable, e.g. "rainfall -28%"
    weight_contribution: float

class RiskEvent(BaseModel):
    event_id: str
    farmer_token: str
    village_id: str
    score: int = Field(ge=0, le=100)
    band: RiskBand
    confidence: float = Field(ge=0, le=1)
    contributors: list[RiskEventContributor]
    action_ids: list[str] = []
    model_version: str
    created_at: datetime
    expires_at: datetime


class AlertCase(BaseModel):
    case_id: str
    event_id: str
    recipient_role: str  # "officer"
    channel: str          # "pwa" | "sms" | "voice"
    sent_at: Optional[datetime] = None
    ack_at: Optional[datetime] = None
    status: CaseStatus = CaseStatus.new
    resolution_code: Optional[str] = None
    notes: Optional[str] = None