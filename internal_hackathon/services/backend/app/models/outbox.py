from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.core.database import Base
from datetime import datetime

class OutboxMessage(Base):
    __tablename__ = 'outbox_messages'

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True)
    farmer_phone = Column(String, index=True)
    channel = Column(String)  # 'sms', 'voice', 'whatsapp'
    content = Column(JSON)
    status = Column(String, default='pending')  # 'pending', 'sent', 'failed'
    retry_count = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    error_log = Column(String, nullable=True)

