from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, JSON, String
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
    evaluated_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime)
    disclaimer = Column(String, nullable=False, default="This is not a credit, loan-default, or insurance score.")
    context_flags = Column(JSON, default=list)
