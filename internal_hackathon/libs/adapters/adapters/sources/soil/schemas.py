from pydantic import BaseModel


class SoilObservation(BaseModel):
    water_holding_capacity: str
