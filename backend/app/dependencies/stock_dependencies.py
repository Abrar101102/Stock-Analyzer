from app.data_providers.yahoo_provider import YahooMarketDataProvider
from app.services.stock_service import StockService
from fastapi import Depends
from sqlalchemy.orm import Session
from app.dependencies.db_dependency import get_db

#Dependency factories
# FastAPI
#    └── get_stock_service()
#             └── get_yahoo_market_data_provider()
#                        └── YahooMarketDataProvider()


def get_yahoo_market_data_provider():#This function is a dependency factory

  return YahooMarketDataProvider()

def get_stock_service(
  yahoo_market_data_provider=Depends(get_yahoo_market_data_provider),
  db: Session = Depends(get_db)
):#This function is a dependency factory
  provider = yahoo_market_data_provider
  return StockService(provider, db)



