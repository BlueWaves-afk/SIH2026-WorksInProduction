from pydantic import BaseModel


class MarketObservation(BaseModel):
    mandi_id: str
    commodity: str
    modal_price: float
    arrivals: float | None = None
