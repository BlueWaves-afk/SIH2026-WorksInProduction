from sqlalchemy import Column, Integer, String, Float, Date
from app.core.database import Base

class MarketQuote(Base):
    __tablename__ = 'market_quotes'

    id = Column(Integer, primary_key=True, index=True)
    commodity = Column(String, index=True)
    mandi_id = Column(String, index=True)
    date = Column(Date)
    modal_price = Column(Float)
    arrivals = Column(Float)
    source = Column(String)
    quality = Column(String)

