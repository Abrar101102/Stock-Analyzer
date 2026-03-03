from sqlalchemy.orm import Session
from app.models.quarterly_snapshot_model import QuarterlyFundamentalSnapshot
from datetime import datetime

class QuarterlyWriteRepository:
  def upsert_snapshot(
      self,
      db:Session,
      symbol:str,
      fiscal_year:int,
      fiscal_quater:int,
      effective_date,
      data:dict
  ):
    existing = (
      db.query(QuarterlyFundamentalSnapshot).
      filter(
        QuarterlyFundamentalSnapshot.symbol == symbol,
        QuarterlyFundamentalSnapshot.fiscal_quarter == fiscal_quater,
        QuarterlyFundamentalSnapshot.fiscal_year == fiscal_year
      ).first()

    )
    if existing:
      existing.data = data
      existing.ingestion_time = datetime.utcnow()
      existing.effective_date = effective_date
      db.commit()
      db.refresh(existing)
      return existing
    
    snapshot = QuarterlyFundamentalSnapshot(
      symbol = symbol,
      fiscal_year = fiscal_year,
      fiscal_quater = fiscal_quater,
      effective_date = effective_date,
      ingestion_time = datetime.utcnow(),
      data = data
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    return snapshot
