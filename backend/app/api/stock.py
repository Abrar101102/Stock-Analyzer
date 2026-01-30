from fastapi import APIRouter,HTTPException,Depends
from app.dependencies.stock_dependencies import get_stock_service
from app.dependencies.fundamental_depencies import get_fundamental_service
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
  
@router.get("/fundamentals/{symbol}/snapshot")
def get_fundamental_snapshot(symbol:str,fundamental_service=Depends(get_fundamental_service)):
  try:
    snapshot = fundamental_service.get_fundamental_snapshot(symbol)
    return {
      "symbol":symbol,
      "fundamental_snapshot":snapshot
    }
  except ValueError as ve:
    raise HTTPException(status_code=404,detail=str(ve))
  
@router.get("/fundamentals/{symbol}")
def get_fundamentals(symbol:str,fundamental_service=Depends(get_fundamental_service),period:str="annual",limit:int=5):
  try:
    fundamentals = fundamental_service.get_fundamentals(symbol,period,limit)

    return {
      "symbol":symbol,
      "fundamentals":fundamentals
    }
  except ValueError as ve:
    raise HTTPException(status_code=404,detail=str(ve))
    

@router.get("/fundamentals/{symbol}/ratios")
def get_ratios(symbol:str,fundamental_service=Depends(get_fundamental_service),period:str="annual",limit:int=5):
  try:
    ratios = fundamental_service.get_ratios(symbol,period,limit)
    return {
      "symbol":symbol,
      "ratios":ratios
    }
  except ValueError as ve:
    raise HTTPException(status_code=404,detail=str(ve))