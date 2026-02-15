import logging
from fastapi import APIRouter,Depends,Query,HTTPException,Response

from app.dependencies.fundamental_depencies import get_fundamental_service
from app.dependencies.rate_limit_dependency import rate_limit
from app.dependencies.auth_dependency import require_api_key,require_pro_key
from app.core.validators import validate_period,validate_limit

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

@router.get("/{symbol}/snapshot",dependencies = [Depends(require_api_key),Depends(rate_limit("snapshot"))],response_model=FundamentalSnapshotV1)
def get_fundamental_snapshot(response:Response,symbol:str,fiscal_year:int=Query(...,gt=1900),
    fundamental_service=Depends(get_fundamental_service)):

    logger.info("Snapshot Request Received",extra = {"symbol":symbol,"Version":"V1"})
    snapshot = fundamental_service.get_fundamental_snapshot(symbol, fiscal_year)
    response.headers["X-RateLimit-Limit"] = 60
    response.headers["X-RateLimit-Remaining"]= 59
    return snapshot_to_v1(snapshot)

@router.get("/{symbol}",dependencies = [Depends(require_api_key),Depends(rate_limit("fundamentals"))],response_model=dict[str,list])
def get_fundamentals(response:Response,symbol:str,period:str=Query("annual",pattern="^(annual|quaterly)$"),
    limit:int=Query(5,gt=0,le=20),fundamental_service=Depends(get_fundamental_service)):

    validate_period(period)
    validate_limit(limit)

    logger.info("Fundamentals Request Received",extra = {"symbol":symbol,"Version":"V1"})
    fundamentals = fundamental_service.get_fundamentals(symbol,period,limit)

    response.headers["X-RateLimit-Limit"] = 60
    response.headers["X-RateLimit-Remaining"]= 59

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

    

@router.get("/{symbol}/ratios",dependencies = [Depends(require_pro_key),Depends(rate_limit("ratios"))],response_model=list[RatioV1])
def get_ratios(response:Response,symbol:str,period:str=Query("annual",pattern="^(annual|quaterly)$"),
    limit:int=Query(5,gt=0,le=20),fundamental_service=Depends(get_fundamental_service)):

    validate_period(period)
    validate_limit(limit)
    
    logger.info("Getting Ratios Request Received",extra = {"symbol":symbol,"Version":"V1"})

    ratios = fundamental_service.get_ratios(symbol,period,limit)
    response.headers["X-RateLimit-Limit"] = 60
    response.headers["X-RateLimit-Remaining"]= 59
    return [ratio_to_v1(r) for r in ratios]