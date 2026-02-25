from datetime import date
from sqlalchemy.orm import Session
from app.fundamentals.repositories.fundamental_write_repository import FundamentalWriteRepository
from app.fundamentals.repositories.fundamental_read_repository import FundamentalReadRepository
from app.core.exceptions import ValidationError,NotFoundError
class FundamentalPersistanceProvider:

  def __init__(self):
    self.write_repo = FundamentalWriteRepository()
    self.read_repo = FundamentalReadRepository()

  def ingest_fundamental_snapshot(
      self,
      db:Session,
      symbol:str,
      fiscal_year:int,
      effective_date:date,
      data:dict
  ):
    #validation 
    if effective_date>date.today():
      raise ValidationError(
        code = "INVALID_FILING_DATE",
        message="Filing Date Cannot be in the future"
      )
    
    if not data:
      raise ValidationError(
        code="EMPTY_DATA",
        message="Fundamental Data Cannot be empty"
      )
    
    existing = self.read_repo.get_latest(db,symbol,fiscal_year)

    if existing and existing.effective_date == effective_date and existing.data == data:
      return existing
    
    return self.write_repo.save_snapshot(
      db=db,
      symbol=symbol,
      fiscal_year=fiscal_year,
      effective_date=effective_date,
      data=data
    )
  
  def fetch_latest(self,db:Session,symbol:str,fiscal_year:int):

    snapshot = self.read_repo.get_latest(db,symbol,fiscal_year)

    if not snapshot:
      raise NotFoundError(
        code="SNAPSHOT_NOT_FOUND",
        message=f"No Snapshot found for {symbol} FY {fiscal_year}"
      )
    
    return snapshot
  
  def fetch_as_of(self,db:Session,symbol:str,fiscal_year:int,as_of_date:date):
    snapshot = self.read_repo.get_as_of(db,symbol,fiscal_year,as_of_date)

    if not snapshot:
      raise NotFoundError(
        code="SNAPSHOT_NOT_FOUND",
        message="No Snapshot available as of requested date."
      )
    return snapshot