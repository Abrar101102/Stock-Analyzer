from dataclasses import asdict
from datetime import date
import json
from app.models.fundamental_snapshot import FundamentalSnapshot
class FundamentalIngestionService:
  def __init__(self,provider_service,persistance_service):
    
    self.provider_service = provider_service
    self.persistance_service = persistance_service

  def json_serial(self,obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")
  
  def ingest_symbol_year(self,db,symbol,fiscal_year):
    snapshot = self.provider_service.get_fundamental_snapshot(
      symbol=symbol,
      fiscal_year=fiscal_year
    )

    snapshot_dict = asdict(snapshot)
    data_dict = json.dumps(snapshot_dict, default=self.json_serial)
    effective_date = snapshot.effective_date

    return self.persistance_service.ingest_fundamental_snapshot(
      db=db,
      symbol=symbol,
      fiscal_year=fiscal_year,
      effective_date=effective_date,
      data=data_dict
    )
  def backfill_symbol_year(self,db,symbol:str):
    stored_years = {
      row.fiscal_year
      for row in db.query(FundamentalSnapshot.fiscal_year).filter(
        FundamentalSnapshot.symbol == symbol
      ).all()
    }
    missing_snapshots = self.provider_service.missing_years_snapshots(symbol,'annual',stored_years)

    missing_years_data =[]
    for snapshot in missing_snapshots:
      ingested = self.persistance_service.ingest_fundamental_snapshot(
        db=db,
        symbol=symbol,
        fiscal_year=snapshot.fiscal_year,
        effective_date=snapshot.effective_date,
        data=asdict(snapshot)
      )
      missing_years_data.append(ingested.fiscal_year)
      
    return missing_years_data
  
      
