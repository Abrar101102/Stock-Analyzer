from typing import Optional,Literal
from dataclasses import dataclass
from datetime import date
from app.fundamentals.models.income_statement_model import IncomeStatementModel
from app.fundamentals.models.cash_flow_model import CashFlowStatementModel
from app.fundamentals.models.balance_sheet_model import BalanceSheetModel

periodType = Literal["annual","quarterly"]

@dataclass
class FundamentalSnapshotModel:
    """ 
    Consolidated, read-optimized snapshot of a company's fundamental data for a given fiscal year.
    """
    # Identification
    symbol: str
    period: periodType
    fiscal_year: int
    effective_date : date
    
    
    # Full statements (compositon)
    income_statement : Optional[IncomeStatementModel]
    cash_flow_statement : Optional[CashFlowStatementModel]
    balance_sheet : Optional[BalanceSheetModel]

    # Key Metrics (flattened for quick access)
    # From Income Sheet Model
    fiscal_quarter:Optional[int]=None
    total_revenue: Optional[float] = None
    net_income:Optional[float] = None
    eps:Optional[float] = None
    # From Cash Flow Model
    operating_cash_flow : Optional[float] = None
    # From Balance Sheet Model 
    total_liabilities : Optional[float] = None
    total_assets : Optional[float] = None
    shareholders_equity : Optional[float] = None