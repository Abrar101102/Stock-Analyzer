from app.models.quarterly_snapshot_model import QuarterlyFundamentalSnapshot
from app.core.logging import trace

class QuarterlyPersistanceService:
  @trace
  def ingest_quarterly_snapshot(
      self,db,symbol,fiscal_year,fiscal_quarter,effective_date,data
  ):
    existing = (
      db.query(QuarterlyFundamentalSnapshot).filter(
      QuarterlyFundamentalSnapshot.symbol == symbol,
      QuarterlyFundamentalSnapshot.fiscal_year == fiscal_year,
      QuarterlyFundamentalSnapshot.fiscal_quarter == fiscal_quarter
    ).first()
    )
    if existing:
      existing.data = data
      existing.effective_date = effective_date
      db.commit()
      db.refresh(existing)
      return existing
    
    new_snapshot = QuarterlyFundamentalSnapshot(
      symbol = symbol,
      fiscal_quarter = fiscal_quarter,
      fiscal_year = fiscal_year,
      effective_date = effective_date,
      data = data
    )
    db.add(new_snapshot)
    db.commit()
    db.refresh(new_snapshot)

    return new_snapshot