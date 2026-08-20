from pydantic import BaseModel


class Coordinate(BaseModel):
    lat: float
    lon: float
