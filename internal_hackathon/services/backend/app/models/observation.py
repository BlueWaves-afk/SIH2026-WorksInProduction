from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String
from app.core.database import Base

class Observation(Base):
    __tablename__ = 'weather_observations'

    id = Column(Integer, primary_key=True, index=True)
    farmer_token = Column(String, index=True, nullable=True)
    source = Column(String)
    observed_at = Column(DateTime)
    village_id = Column(String, index=True)
    metric = Column(String)
    value = Column(JSON)
    unit = Column(String)
    quality = Column(String)
    ttl = Column(Integer)  # seconds, kept as an integer at the storage boundary
    plot_grid = Column(String, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
