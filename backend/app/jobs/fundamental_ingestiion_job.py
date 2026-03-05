from datetime import date
from app.db.session import SessionLocal
from app.services.fundamental_ingestion_service import FundamentalIngestionService
from app.dependencies.fundamental_persistance_dependency import get_fundamental_persistance_service
from app.dependencies.fundamental_depencies import get_fundamental_service,get_yahoo_fundamental_provider
from app.services.quarterly_ingestion_service import QuarterlyIngestionService
from app.dependencies.quarterly_persistance_dependecy import get_quarterly_fundamental_persistance_service

from app.registry.stock_registry import StockRegistry

def run__fundamental_ingestion():

  db = SessionLocal()

  try:
    yahoo_provider = get_yahoo_fundamental_provider()
    provider_service = get_fundamental_service(yahoo_fundamental_provider=yahoo_provider)
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
          symbol=stock.yahoo_symbol,
          fiscal_year=current_year
        )
        quarterly_ingestion_service.backfill_symbol_quarters(
          db=db,
          symbol=stock.yahoo_symbol
        
         )
      except Exception as e:
        db.rollback()
        continue
    db.commit()
  except Exception as e:
    db.rollback()
    raise
  finally:
    db.close()