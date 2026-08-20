from sqlalchemy import Column, Integer, String, DateTime, JSON
from app.core.database import Base
from datetime import datetime

class ConsentLedger(Base):
    __tablename__ = 'consent_ledger'

    id = Column(Integer, primary_key=True, index=True)
    farmer_token = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String) # 'GRANT' or 'WITHDRAW'
    purpose = Column(String) # 'store_data', 'contact_me', 'use_analytics'
    proof = Column(JSON)

