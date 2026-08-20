from pydantic import BaseModel


class CropStressObservation(BaseModel):
    ndvi_anomaly_pct: float
    ndwi_anomaly_pct: float = 0
