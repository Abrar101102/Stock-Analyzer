from datetime import date
from sqlalchemy.orm import Session
from app.fundamentals.mappers.fundamental_snapshot_mapper import FundamentalSnapshotMapper
from app.fundamentals.repositories.fundamental_read_repository import FundamentalReadRepository
from app.registry.stock_registry import StockRegistry
from app.core.exceptions import NotFoundException

class FundamentalReadService:
  def __init___(self):
    self.repository = FundamentalReadRepository()
      
  def get_snapshot(
      self,
      db:Session,
      symbol:str,
      fiscal_year:int,
      as_of_date:date|None =None):
    if not StockRegistry.exists(symbol):
      raise NotFoundException(
        code = "STOCK_NOT_FOUND",
        message = f"Stock with symbol '{symbol}' not found in registry"
      )
    if as_of_date:
      entity = self.repository.get_as_of(db,symbol,fiscal_year,as_of_date)
    else:
      entity = self.repository.latest(db,symbol,fiscal_year)

    if not entity:
      return None
    
    return FundamentalSnapshotMapper.to_domain(entity)
  


