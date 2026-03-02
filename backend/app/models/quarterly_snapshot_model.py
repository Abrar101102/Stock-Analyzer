from sqlalchemy import Column,Integer,String,Date,DateTime,JSON
from sqlalchemy.orm import declarative_base
from app.db.base_class import Base

class QuarterlyFundamentalSnapshot(Base):
  __tablename__ = "quarterly_fundamental_snapshot"

  id = Column(Integer,primary_key=True,autoincrement=True)
  symbol = Column(String,index=True)
  fiscal_year = Column(Integer)
  fiscal_quarter = Column(Integer)
  effective_date = Column(Date)
  ingestion_time = Column(DateTime)
  data = Column(JSON)