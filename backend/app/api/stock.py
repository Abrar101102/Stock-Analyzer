from fastapi import APIRouter,HTTPException,Depends
from app.dependencies.stock_dependencies import get_stock_service
from app.dependencies.fundamental_dependencies import get_fundamental_service
# from app.services.stock_service import StockService
# from app.data_providers.yahoo_provider import YahooMarketDataProvider

router = APIRouter(prefix="/stock",tags=["Stock"])

# yahoo_market_data_provider = YahooMarketDataProvider()# instance of class
# stock_service = StockService(yahoo_market_data_provider)# instance of class 

@router.get("/ping")
def ping():
  return {"message":"Stock endpoint is reachable"}


@router.get("/{symbol}/price-history/")
def get_price_history(symbol:str,stock_service=Depends(get_stock_service),period:str="6mo"):
  try:
    history = stock_service.get_price_history(symbol,period)
    return {"symbol":symbol,"price History of period":period,"data":history}

  except ValueError as ve:
    raise HTTPException(status_code=404,detail=str(ve))
  
