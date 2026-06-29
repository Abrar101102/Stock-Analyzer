from fastapi  import APIRouter,Depends
from sqlalchemy.orm import Session
from app.dependencies.db_dependency import get_db
from app.fundamentals.models.quarterly_schema import quarterlyTrendResponse
from app.services.quarterly_trend_service import QuarterlyTrendService
from app.core.logging import trace

router = APIRouter(prefix ="/quarterly",tags= ["quarterly Trends"])

@router.get("/{symbol}",response_model = quarterlyTrendResponse)
@trace
def get_quarterly_trends(symbol:str,db:Session=Depends(get_db)):
  service = QuarterlyTrendService()

  result = service.build_quarterly_snapshot(db,symbol)

  return result