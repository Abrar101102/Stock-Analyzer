from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from dependencies.db_dependency import get_db

from backend.app.services.valuation_service import ValuationService
from app.market_data.base_price_service import BasePriceService

router = APIRouter("/valuation",tags=["Valuation"])

price_service = BasePriceService() 

@router.get("/{symbol}")
def get_valuation(symbol:str,db:Session=Depends(get_db)):
  service = ValuationService(price_service)
  try:
    return service.get_valuation(db,symbol)
  except Exception as e:
    return {"error": str(e)}
