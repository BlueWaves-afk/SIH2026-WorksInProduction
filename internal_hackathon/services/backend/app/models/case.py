from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class AlertCase(Base):
    __tablename__ = 'alert_cases'

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, index=True)
    recipient_role = Column(String)
    channel = Column(String)
    sent_at = Column(DateTime)
    ack_at = Column(DateTime, nullable=True)
    status = Column(String) # New, Acknowledged, Visited, Resolved
    resolution_code = Column(String, nullable=True)
    notes = Column(String, nullable=True)

