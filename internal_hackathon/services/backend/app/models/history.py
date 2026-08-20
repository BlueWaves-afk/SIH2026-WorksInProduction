from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String

from app.core.database import Base


class CaseStatusHistory(Base):
    __tablename__ = "case_status_history"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, index=True, nullable=False)
    from_status = Column(String, nullable=True)
    to_status = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DeliveryAttempt(Base):
    __tablename__ = "delivery_attempts"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, index=True, nullable=False)
    channel = Column(String, nullable=False)
    status = Column(String, nullable=False)
    provider_reference = Column(String, nullable=True)
    error = Column(String, nullable=True)
    attempted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
