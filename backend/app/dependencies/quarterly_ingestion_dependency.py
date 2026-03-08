from app.services.quarterly_persistance import QuarterlyPersistanceService
from app.services.quarterly_ingestion_service import QuarterlyIngestionService
from app.fundamentals.data_providers.fallback_fundamental_provider import FallbackFundamentalProvider
from app.services.fundamental_service import FundamentalService

provider = FallbackFundamentalProvider()


def get_quarterly_ingestion_service(
    provider_service = FundamentalService(provider),
    persistance_service = QuarterlyPersistanceService()
):
  return QuarterlyIngestionService(
    provider_service=provider_service,
    persistance_service=persistance_service
  )