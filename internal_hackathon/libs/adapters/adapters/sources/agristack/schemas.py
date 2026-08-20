from pydantic import BaseModel


class FarmerPrefill(BaseModel):
    farmer_ref: str
    village_id: str
    crop: str | None = None
