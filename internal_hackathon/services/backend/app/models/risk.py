from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from app.core.database import Base

class RiskEvent(Base):
    __tablename__ = 'risk_events'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True)
    farmer_token = Column(String, index=True)
    village_id = Column(String, index=True)
    score = Column(Float)
    band = Column(String)  # Green, Amber, Red
    confidence = Column(Float)
    contributors = Column(JSON)
    action_ids = Column(JSON)
    model_version = Column(String)
    expires_at = Column(DateTime)

