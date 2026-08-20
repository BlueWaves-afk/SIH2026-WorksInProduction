from sqlalchemy import Column, Integer, String
from geoalchemy2 import Geometry
from app.core.database import Base

class Village(Base):
    __tablename__ = 'villages'

    id = Column(Integer, primary_key=True, index=True)
    village_id = Column(String, unique=True, index=True)
    district_id = Column(String, index=True)
    name = Column(String)
    location = Column(Geometry('POINT'))

class Mandi(Base):
    __tablename__ = 'mandis'

    id = Column(Integer, primary_key=True, index=True)
    mandi_id = Column(String, unique=True, index=True)
    name = Column(String)
    location = Column(Geometry('POINT'))

