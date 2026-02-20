from fastapi import APIRouter,Depends,Query,HTTPException
from sqlalchemy.orm import Session
from datetime import date
from app.dependencies.db_dependency import get_db
from app.services.fundamental_read_service import FundamentalReadService

router =APIRouter(prefix='/fundamentals',tags=['Fundamentals'])

service = FundamentalReadService()

@router.get("/{symbol}/{fiscal_year}")
def get_fundamental_snapshot(symbol:str,fiscal_year:int,as_of:date|None = Query(default=None),db:Session = Depends(get_db)):
  try:
    snapshot = service.get_snapshot(db,symbol,fiscal_year,as_of)

    if not snapshot:
      raise HTTPException(status_code=404,detail="Snapshot not found")
    
    return snapshot
  
  except Exception as e:
    raise HTTPException(status_code=500,detail=str(e))
  
@router.get("/{symbol}/{fiscal_year}/income")
def get_income_statement(
  symbol:str,
  fiscal_year:int,
  as_of :date |None = None,
  db:Session = Depends(get_db)):

  entity = service.get_snapshot(db,symbol,fiscal_year,as_of)

  if not entity or not entity.income_statement:
    raise HTTPException(status_code=404,detail="Income Statement not found for given parameters.")
  
  return entity.income_statement
            
@router.get("/{symbol}/{fiscal_year}/balance_sheet")
def get_balance_sheet(
  symbol:str,
  fiscal_year:int,
  as_of :date |None = None,
  db:Session = Depends(get_db)):

  entity = service.get_snapshot(db,symbol,fiscal_year,as_of)

  if not entity or not entity.balance_sheet:
    raise HTTPException(status_code=404,detail="Balance Sheet not found for given parameters.")
  
  return entity.balance_sheet