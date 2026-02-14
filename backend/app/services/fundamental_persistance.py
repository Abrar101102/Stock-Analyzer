from datetime import date
from sqlalchemy.orm import Session
from app.repository.fundamental_repository import save_snapshot,get_latest_snapshot,get_snapshot_as_of
from app.core.exceptions import ValidationError,NotFoundError
class FundamentalPersistanceProvider:

  def ingest_fundamental_snapshot(
      db:Session,
      symbol:str,
      fiscal_year:int,
      filing_date:date,
      data:dict
  ):
    #validation 
    if filing_date<date.today():
      raise ValidationError(
        code = "INVALID_FILING_DATE",
        message="Filing Date Cannot be in the future"
      )
    
    if not data:
      raise ValidationError(
        code="EMPTY_DATA",
        message="Fundamental Data Cannot be empty"
      )
    
    existing = get_latest_snapshot(db,symbol,fiscal_year)

    if existing and existing.filing_date == filing_date and existing.data == data:
      return existing
    
    return save_snapshot(
      db=db,
      symbol=symbol,
      fiscal_year=fiscal_year,
      filing_date=filing_date,
      data=data
    )
  
  def fetch_latest(db:Session,symbol:str,fiscal_year:int):

    snapshot = get_latest_snapshot(db,symbol,fiscal_year)

    if not snapshot:
      raise NotFoundError(
        code="SNAPSHOT_NOT_FOUND",
        message=f"No Snapshot found for {symbol} FY {fiscal_year}"
      )
    
    return snapshot
  
  def fetch_as_of(db:Session,symbol:str,fiscal_year:int,as_of_date:date):
    snapshot = get_snapshot_as_of(db,symbol,fiscal_year,as_of_date)

    if not snapshot:
      raise NotFoundError(
        code="SNAPSHOT_NOT_FOUND",
        message="No Snapshot available as of requested date."
      )
    return snapshot