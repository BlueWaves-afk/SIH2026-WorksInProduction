from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConsentFlags(BaseModel):
    store_data: bool = False
    contact_me: bool = False
    whatsapp_call: bool = False
    email_alerts: bool = False
    use_analytics: bool = False
    due_window: bool = False


class FarmerProfileCreate(BaseModel):
    farmer_token: str | None = Field(default=None, min_length=3, max_length=128)
    village_id: str = Field(min_length=1, max_length=128)
    locale: str = Field(default="en", min_length=2, max_length=8)
    crop: str = Field(min_length=1, max_length=64)
    secondary_crop: str | None = Field(default=None, max_length=64)
    sowing_date: date
    irrigation_type: str = Field(default="rainfed", pattern="^(rainfed|partial|assured)$")
    area_band: str = Field(default="<1", pattern="^(<1|1-2|>2)$")
    institutional_access: str = Field(default="unknown", pattern="^(good|limited|unknown)$")
    soil_retention: str = Field(default="unknown", pattern="^(poor|medium|good|unknown)$")
    schemes_enrolled: list[str] = Field(default_factory=list, max_length=20)
    phone: str | None = Field(default=None, max_length=32, repr=False)
    email: str | None = Field(default=None, max_length=254, repr=False, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    consent_flags: ConsentFlags = Field(default_factory=ConsentFlags)

    @field_validator("email", mode="before")
    @classmethod
    def _blank_email_is_none(cls, value: object) -> object:
        # Onboarding may submit an empty string when the farmer skips email;
        # normalise blanks to None so the pattern only validates real addresses.
        if isinstance(value, str):
            cleaned = value.strip().lower()
            return cleaned or None
        return value


class FarmerProfile(FarmerProfileCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    farmer_token: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class FarmerProfilePublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    farmer_token: str
    village_id: str
    locale: str
    crop: str
    secondary_crop: str | None = None
    sowing_date: date
    irrigation_type: str
    area_band: str
    institutional_access: str
    soil_retention: str
    schemes_enrolled: list[str] = Field(default_factory=list)
    consent_flags: ConsentFlags
