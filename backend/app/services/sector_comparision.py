from app.registry.stock_registry import StockRegistry
from app.core.exceptions import NotFoundError
from sqlalchemy.orm import Session
import statistics


class SectorComparisionService:
  def __init__(self,valuation_service,trend_service):
    self.valuation_service = valuation_service
    self.trend_service = trend_service

  def compare_pe_ratio(self,db:Session,symbol:str):
    peers = StockRegistry.get_peers(symbol,db)

    values = []
    for peer in peers:
      pe = self.valuation_service.get_pe_ratio(db,peer.symbol)
      values.append((peer.symbol,pe))

    if not values:
      raise NotFoundError(
        code = "NO_PEERS_FOUND",
        message=f"No peers found for symbol {symbol}"
      )
    
    company_value = dict(values).get(symbol)
    numbers = [v for _,v in values if v is not None]

    sector_avg = statistics.mean(numbers)
    ranked = sorted(values,key = lambda x:x[1])
    rank = [s for s,_ in ranked].index(symbol) + 1

    below = len([v for v in numbers if v < company_value])
    percentile = below/len(numbers)*100

    return {
      "company_value": company_value,
      "sector_average": sector_avg,
      "rank": rank,
      "percentile": percentile,
      "total_peers": len(numbers)
    }