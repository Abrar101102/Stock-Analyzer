from datetime import datetime
from sqlalchemy import Column, Date, DateTime, Float, Integer, JSON, String, Text, UniqueConstraint, Index
from app.db.base_class import Base


class ThesisCache(Base):
  __tablename__ = "thesis_cache"

  id = Column(Integer, primary_key=True, autoincrement=True)
  symbol = Column(String, index=True, nullable=False)
  date = Column(Date, nullable=False)
  verdict = Column(String, nullable=False)
  composite_score = Column(Float, nullable=False)
  summary = Column(Text, nullable=False)
  signals = Column(JSON, nullable=False)
  generated_at = Column(DateTime, nullable=False)
  created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
  updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

  __table_args__ = (
    UniqueConstraint("symbol", "date", name="uix_symbol_date_thesis_cache"),
    Index("idx_symbol_date_thesis_cache", "symbol", "date"),
  )
