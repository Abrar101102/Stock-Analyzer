from fastapi import Depends
from app.fundamentals.data_providers.yahoo_fundamental_provider import YahooFundamentalProvider
from app.services.fundamental_service import FundamentalService

def get_yahoo_fundamental_provider():
  return YahooFundamentalProvider()

def get_fundamental_service(yahoo_fundamental_provider=Depends(get_yahoo_fundamental_provider)):
  provider = yahoo_fundamental_provider
  return FundamentalService(provider)