from datetime import date
from app.db.session import SessionLocal
from app.services.fundamental_ingestion_service import FundamentalIngestionService
from app.dependencies.fundamental_persistance_dependency import get_fundamental_persistance_service
from app.dependencies.fundamental_dependencies import get_fundamental_service,get_fallback_fundamental_provider
from app.services.quarterly_ingestion_service import QuarterlyIngestionService
from app.dependencies.quarterly_persistance_dependecy import get_quarterly_fundamental_persistance_service

from app.registry.stock_registry import StockRegistry

def run__fundamental_ingestion():

  db = SessionLocal()

  try:
    fallback_provider = get_fallback_fundamental_provider()
    provider_service = get_fundamental_service(fallback_fundamental_provider=fallback_provider)
    persistance_service = get_fundamental_persistance_service()

    ingestion_service = FundamentalIngestionService(
      provider_service=provider_service,
      persistance_service=persistance_service
    )

    quarterly_persistance_service = get_quarterly_fundamental_persistance_service()
    quarterly_ingestion_service = QuarterlyIngestionService(
      provider_service=provider_service,
      persistance_service=quarterly_persistance_service
    )

    current_year = date.today().year -1
    stocks = StockRegistry.list_all()

    for stock in stocks.values():
      try:
        ingestion_service.ingest_symbol_year(
          db = db,
          symbol=stock.symbol,
          fiscal_year=current_year
        )

        quarterly_ingestion_service.backfill_symbol_quarters(
          db=db,
          symbol=stock.symbol
        
         )
      except Exception as e:
        import traceback
        print(f"FAILED for {stock.symbol}: {type(e).__name__}: {e}")
        traceback.print_exc()  # ← THIS will show the exact line crashing
        db.rollback()
        continue
    db.commit()
  except Exception as e:
    db.rollback()
    raise
  finally:
    db.close()