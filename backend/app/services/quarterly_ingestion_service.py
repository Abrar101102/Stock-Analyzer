from dataclasses import asdict, is_dataclass
from datetime import date
import json
from app.models.quarterly_snapshot_model import QuarterlyFundamentalSnapshot
from app.core.logging import trace

class QuarterlyIngestionService:
  def __init__(self,provider_service,persistance_service):
    self.provider_service = provider_service
    self.persistance_service = persistance_service

  def json_serial(self,obj):
    if isinstance(obj,date):
      return obj.isoformat()
    if is_dataclass(obj):
        return asdict(obj)

    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Type {type(obj)} is not serializable")
  
  @trace
  def ingest_symbol_quarter(self,db,symbol:str,fiscal_year:int,fiscal_quarter:int):
    snapshot = self.provider_service.get_quarterly_income_snapshot(
      symbol=symbol,
      fiscal_year=fiscal_year,
      fiscal_quarter=fiscal_quarter
    )

    snapshot_dict = asdict(snapshot)

    data_dict = json.dumps(snapshot_dict,default=self.json_serial)

    return self.persistance_service.ingest_quarterly_snapshot(
      db=db,
      symbol=symbol,
      fiscal_year=fiscal_year,
      fiscal_quarter=fiscal_quarter,
      effective_date = snapshot.effective_date,
      data = data_dict
    )
  
  @trace
  def backfill_symbol_quarters(self,db,symbol:str):

    stored_quarters = {
      (row.fiscal_year,row.fiscal_quarter)
      for row in db.query(QuarterlyFundamentalSnapshot.fiscal_quarter,QuarterlyFundamentalSnapshot.fiscal_year).
      filter(
        QuarterlyFundamentalSnapshot.symbol == symbol
      ).all()
    }
    missing_snapshots = self.provider_service.missing_years_snapshots(
      symbol=symbol,
      period = "quarter",
      stored_periods = stored_quarters
      )
    
    ingested_periods = []
    print(f"Backfilling Missing Quarters for {symbol}: {missing_snapshots}")

    for snapshot in missing_snapshots:
      ingested = self.persistance_service.ingest_quarterly_snapshot(
        db=db,
        symbol = snapshot["symbol"],
        fiscal_year = snapshot["fiscal_year"],
        fiscal_quarter = snapshot["fiscal_quarter"],
        effective_date = snapshot["effective_date"],
        data = json.dumps(snapshot, default=self.json_serial)
        
      )

      ingested_periods.append(
        (ingested.fiscal_year,ingested.fiscal_quarter)
      )
    return ingested_periods