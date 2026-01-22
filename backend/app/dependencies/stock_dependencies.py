from app.data_providers.yahoo_provider import YahooMarketDataProvider
from app.services.stock_service import StockService
from fastapi import Depends

def get_yahoo_market_data_provider():
  return YahooMarketDataProvider()

def get_stock_service(yahoo_market_data_provider=Depends(get_yahoo_market_data_provider)):
  provider = yahoo_market_data_provider
  return StockService(provider)



