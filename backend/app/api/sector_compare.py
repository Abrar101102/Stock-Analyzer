from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from app.dependencies.db_dependency import get_db
from app.services.sector_comparision import SectorComparisionService
from app.services.valuation_service import ValuationService
from app.market_data.base_price_service import BasePriceService

router = APIRouter("/sector-compare",tags = ["Sector Comparison"])

price_Service = BasePriceService()

@router.get("/{symbol}/{fiscal_year}")
def compare_sector(symbol:str,fiscal_year:int,db:Session=Depends(get_db)):
  try:

    ValuationService = ValuationService(price_Service)
    TrendService = None
    service = SectorComparisionService(ValuationService,TrendService)


    result = service.compare_pe_ratio(db,symbol)

    return result
  except Exception as e:
    return {"error": str(e)}