from fastapi import Depends,Query,APIRouter
from sqlalchemy.orm import Session
from app.dependencies.db_dependency import get_db
from app.services.trend_service import TrendService

router = APIRouter(prefix="/trends",tags=["trends"])

service = TrendService()

@router.get("/{symbol}")
def get_trends(symbol:str,limit:int = Query(default=5),db:Session = Depends(get_db)):
  return service.get_trends(db=db,symbol=symbol,limit=limit)