from datetime import date
from app.db.session import SessionLocal
from app.services.fundamental_ingestion_service import FundamentalIngestionService
from app.dependencies.fundamental_persistance_dependency import get_fundamental_persistance_service
from app.dependencies.fundamental_depencies import get_fundamental_service
from app.registry.stock_registry import StockRegistry

def run__fundamental_ingestion():

  db = SessionLocal()

  try:
    provider_service = get_fundamental_service()
    persistance_service = get_fundamental_persistance_service()

    ingestion_service = FundamentalIngestionService(
      provider_service=provider_service,
      persistance_service=persistance_service
    )

    current_year = date.today().year -1
    stocks = StockRegistry.list_all()

    for stock in stocks.values():
      ingestion_service.ingest_symbol_year(
        db = db,
        symbol=stock.symbol,
        fiscal_year=current_year
      )
    db.commit()
  except Exception as e:
    db.rollback()
    raise
  finally:
    db.close()