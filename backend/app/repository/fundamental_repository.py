from datetime import datetime
from sqlalchemy.orm import Session
from app.models.fundamental_snapshot import FundamentalSnapshot

def save_snapshot(
    db:Session,
    symbol:str,
    fiscal_year:int,
    filing_date,
    data:dict
):
  snapshot = FundamentalSnapshot(
    symbol = symbol,
    fiscal_year= fiscal_year,
    filing_date=filing_date,
    ingestion_time= datetime.now(),
    data=data
  )

  db.add(snapshot)
  db.commit()
  db.refresh(snapshot)

  return snapshot

def get_latest_snapshot(
    db:Session,
    symbol:str,
    fiscal_year:int
):
  return (
    db.query(FundamentalSnapshot).filter(
      FundamentalSnapshot.symbol == symbol,
      FundamentalSnapshot.fiscal_year == fiscal_year
    )
    .order_by(FundamentalSnapshot.ingestion_time.desc())
    .first()
  )

def get_snapshot_as_of(
    db:Session,
    symbol:str,
    fiscal_year:int,
    as_of_date
):
  return (
    db.query(FundamentalSnapshot)
    .filter(
      FundamentalSnapshot.symbol == symbol,
      FundamentalSnapshot.fiscal_year == fiscal_year,
      FundamentalSnapshot.filing_date <= as_of_date 
    )
    .order_by(FundamentalSnapshot.filing_date.desc())
    .first()
  )