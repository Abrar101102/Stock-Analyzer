from datetime import datetime
from sqlalchemy.orm import Session
from app.models.fundamental_snapshot import FundamentalSnapshot

class FundamentalWriteRepository:
  def save_snapshot(
    self,
    db:Session,
    symbol:str,
    fiscal_year:int,
    effective_date,
    data:dict
):
    
    existing = db.query(FundamentalSnapshot).filter(
    FundamentalSnapshot.symbol == symbol,
    FundamentalSnapshot.fiscal_year == fiscal_year
  ).first()

    if existing:
      existing.data = data
      existing.effective_date = effective_date
      existing.ingestion_time = datetime.utcnow()
      db.commit()
      db.refresh(existing)
      return existing
    snapshot = FundamentalSnapshot(
      symbol = symbol,
      fiscal_year= fiscal_year,
      effective_date=effective_date,
      ingestion_time= datetime.now(),
      data=data
    )

    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)

    return snapshot
