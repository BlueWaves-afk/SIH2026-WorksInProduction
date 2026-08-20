from sqlalchemy import Column, Integer, String, Float, DateTime
from app.core.database import Base

class Observation(Base):
    __tablename__ = 'weather_observations'

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String)
    observed_at = Column(DateTime)
    village_id = Column(String, index=True)
    metric = Column(String)
    value = Column(Float)
    unit = Column(String)
    quality = Column(String)
    ttl = Column(Integer)

