from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.core.database import Base
from datetime import datetime

class AuditEvent(Base):
    __tablename__ = 'audit_events'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    actor_id = Column(String, index=True)
    actor_role = Column(String)
    action = Column(String)
    target_id = Column(String, index=True)
    details = Column(JSON)
    ip_address = Column(String, nullable=True)

