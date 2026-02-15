from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session
from datetime import date

from app.dependencies.db_dependency import get_db
from app.dependencies.fundamental_persistance_dependency import get_fundamental_persistance_service
from app.dependencies.fundamental_ingestion_dependency import get_ingestion_service

router = APIRouter(
  prefix="/internal/fundamentals",
  tags=["Fundamental Persistance"]
)

@router.post("/ingest/{symbol}/{fiscal_year}")
def ingest_snapshot(
    symbol:str,
    fiscal_year:int,
    db:Session = Depends(get_db),
    service = Depends(get_ingestion_service)
):
  return service.ingest_symbol_year(
    db=db,
    symbol=symbol,
    fiscal_year=fiscal_year,
  )

@router.get("/{symbol}/{fiscal_year}/latest")
def get_latest(
    symbol:str,
    fiscal_year:int,
    db:Session=Depends(get_db),
    service=Depends(get_fundamental_persistance_service)
):
  return service.fetch_latest(
    db=db,
    symbol=symbol,
    fiscal_year=fiscal_year
  )

@router.get("/{symbol}/{fiscal_year}")
def get_as_of(
    symbol:str,
    fiscal_year:int,
    as_of:date,
    db:Session=Depends(get_db),
    service=Depends(get_fundamental_persistance_service)
):
  return service.fetch_as_of(
    db=db,
    symbol=symbol,
    fiscal_year=fiscal_year,
    as_of_date=as_of
  )