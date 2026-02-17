from dataclasses import dataclass
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column,Date,Integer,String,DateTime,JSON

Base = declarative_base()

class FundamentalSnapshot(Base):
  __tablename__= "fundamental_snapshot"

  id =  Column(Integer,primary_key=True,autoincrement=True)
  symbol = Column(String,index=True)
  fiscal_year=Column(Integer)
  effective_date= Column(Date)
  ingestion_time = Column(DateTime)
  data = Column(JSON)
