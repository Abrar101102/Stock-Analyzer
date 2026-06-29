from fastapi import APIRouter,Depends,Query
from sqlalchemy.orm import Session
from app.dependencies.db_dependency import get_db
from app.services.derived_metrics_service import DerivedMetricsService
from app.core.logging import trace

router = APIRouter( prefix="/ratios", tags=["derived_metrics"])

service = DerivedMetricsService()

@router.get("/{symbol}")
@trace
def get_ratios(symbol:str,limit:int = Query(default=5),db:Session =Depends(get_db)):
  return service.get_ratios(db,symbol,limit)
