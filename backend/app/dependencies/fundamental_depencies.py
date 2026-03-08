from fastapi import Depends
from app.fundamentals.data_providers.fallback_fundamental_provider import FallbackFundamentalProvider
from app.services.fundamental_service import FundamentalService

def get_fallback_fundamental_provider():
  return FallbackFundamentalProvider()

def get_fundamental_service(fallback_fundamental_provider=Depends(get_fallback_fundamental_provider)):
  provider = fallback_fundamental_provider
  return FundamentalService(provider)