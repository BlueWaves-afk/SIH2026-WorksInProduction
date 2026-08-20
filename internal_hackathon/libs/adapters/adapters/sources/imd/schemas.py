from pydantic import BaseModel


class IMDObservation(BaseModel):
    rainfall_deviation_pct: float
