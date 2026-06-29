from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.dependencies.db_dependency import get_db
from app.services.sector_comparision import SectorComparisionService
from app.services.valuation_service import ValuationService
from app.market_data.base_price_service import BasePriceService
from app.core.logging import trace

router = APIRouter("/sector-compare",tags = ["Sector Comparison"])

price_Service = BasePriceService()

@router.get("/{symbol}/{fiscal_year}")
@trace
def compare_sector(symbol:str,fiscal_year:int,db:Session=Depends(get_db)):
  try:

    ValuationService = ValuationService(price_Service)
    from app.services.trend_service import TrendService
    trend_service = TrendService()
    service = SectorComparisionService(ValuationService, trend_service)

    result = service.compare_all_metrics(db, symbol)

    return result
  except Exception as e:
    return {"error": str(e)}