from pydantic import BaseModel


class MSPReference(BaseModel):
    commodity: str
    price: float
    effective_from: str
