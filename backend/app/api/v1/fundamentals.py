import logging
from fastapi import APIRouter,Depends,Query,HTTPException

from app.dependencies.fundamental_depencies import get_fundamental_service

from app.api.v1.schemas import (
  FundamentalSnapshotV1,
  IncomeStatementV1,
  BalanceSheetV1,
  CashFlowV1,
  RatioV1
)

from app.api.v1.mappers import (
  snapshot_to_v1,
  income_statement_to_v1,
  balance_sheet_to_v1,
  cash_flow_to_v1,
  ratio_to_v1
)

logger = logging.getLogger(__name__)

router = APIRouter(
  prefix='/v1/fundamentals',
  tags=['Fundamentals v1']
  )

@router.get("/{symbol}/snapshot",response_model=FundamentalSnapshotV1)
def get_fundamental_snapshot(symbol:str,fiscal_year:int=Query(...,gt=1900),
    fundamental_service=Depends(get_fundamental_service)):

    logger.info("Snapshot Request Received",extra = {"symbol":symbol,"Version":"V1"})
    snapshot = fundamental_service.get_fundamental_snapshot(symbol, fiscal_year)
    return snapshot_to_v1(snapshot)

@router.get("/{symbol}",response_model=dict[str,list])
def get_fundamentals(symbol:str,period:str=Query("annual",pattern="^(annual|quaterly)$"),
    limit:int=Query(5,gt=0,le=20),fundamental_service=Depends(get_fundamental_service)):

    logger.info("Fundamentals Request Received",extra = {"symbol":symbol,"Version":"V1"})
    fundamentals = fundamental_service.get_fundamentals(symbol,period,limit)

    return {
      "income_statements":[
        income_statement_to_v1(x) for x in fundamentals.income_statements
      ],
      "balance_statements":[
        balance_sheet_to_v1(x) for x in fundamentals.balance_sheets
      ],
      "cash_flows":[
        cash_flow_to_v1(x) for x in fundamentals.cash_flows
      ]
    }

    

@router.get("/{symbol}/ratios",response_model=list[RatioV1])
def get_ratios(symbol:str,period:str=Query("annual",pattern="^(annual|quaterly)$"),
    limit:int=Query(5,gt=0,le=20),fundamental_service=Depends(get_fundamental_service)):
    
    logger.info("Getting Ratios Request Received",extra = {"symbol":symbol,"Version":"V1"})

    ratios = fundamental_service.get_ratios(symbol,period,limit)
    return [ratio_to_v1(r) for r in ratios]