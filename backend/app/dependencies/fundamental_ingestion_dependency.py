from app.services.fundamental_persistance import FundamentalPersistanceProvider

from app.services.fundamental_service import FundamentalService
from app.services.fundamental_ingestion_service import FundamentalIngestionService
from app.fundamentals.data_providers.fallback_fundamental_provider import FallbackFundamentalProvider

provider = FallbackFundamentalProvider()

def get_ingestion_service(
    
    provider_service = FundamentalService(provider),
    persistance_service = FundamentalPersistanceProvider()
):
  return FundamentalIngestionService(
    provider_service=provider_service,
    persistance_service=persistance_service
  )