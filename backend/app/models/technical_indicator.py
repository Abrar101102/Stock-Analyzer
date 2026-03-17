from sqlalchemy import Column,Integer,String,Float,JSON,Date,DateTime,UniqueConstraint,Index
from app.db.base_class import Base
from datetime import datetime

class TechnicalIndicator(Base):
  __tablename__ = "technical_indicators"

  id = Column(Integer,primary_key=True,autoincrement = True)
  symbol = Column(String,index=True)
  date = Column(Date,nullable= False)

  #moving averages
  sma_20 = Column(Float,nullable=True)
  sma_50 = Column(Float,nullable=True)
  sma_200 = Column(Float,nullable=True)
  ema_12 = Column(Float,nullable=True)
  ema_26 = Column(Float,nullable=True)

  #RSI 
  rsi_14 = Column(Float,nullable=True)

  macd_line = Column(Float,nullable=True)
  macd_signal = Column(Float,nullable=True)
  macd_histogram = Column(Float,nullable=True)

  #Bollinger Bands
  bb_upper = Column(Float,nullable=True)
  bb_middle = Column(Float,nullable=True)
  bb_lower = Column(Float,nullable=True)

  #vwap
  vwap = Column(Float,nullable=True)

  #Support or resistance levels
  support_level = Column(Float,nullable=True)
  resistance_level = Column(Float,nullable=True)

  #metadata
  computed_at = Column(DateTime,default=datetime.utcnow)

  __table_args__ = (
    UniqueConstraint('symbol','date',name='uix_symbol_date_indicator'),
    Index('idx_symbol_date_indicator','symbol','date')
  )