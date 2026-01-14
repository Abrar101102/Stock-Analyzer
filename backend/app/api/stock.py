from fastapi import APIRouter
from app.services.stock_service import StockService

router = APIRouter(prefix="/stock",tags=["Stock"])
stock_service = StockService()# instance of class StockService

@router.get("/ping")
def ping():
  return {"message":"Stock endpoint is reachable"}

@router.get("/{symbol}")
def get_symbol_basic_info(symbol:str):
  return stock_service.get_basic_info(symbol)