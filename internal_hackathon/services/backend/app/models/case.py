from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from app.core.database import Base

class AlertCase(Base):
    __tablename__ = 'alert_cases'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, index=True)
    farmer_token = Column(String, index=True, nullable=True)
    village_id = Column(String, index=True, nullable=True)
    recipient_role = Column(String)
    channel = Column(String)
    sent_at = Column(DateTime)
    ack_at = Column(DateTime, nullable=True)
    status = Column(String) # New, Acknowledged, Visited, Resolved
    band = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    assigned_to = Column(String, nullable=True)
    sla_due_at = Column(DateTime, nullable=True)
    sla_breached = Column(String, default="false", nullable=False)
    sla_breached_at = Column(DateTime, nullable=True)
    resolution_code = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
