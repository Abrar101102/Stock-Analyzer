from typing import Optional
from dataclasses import dataclass
from app.models.fundamentals.income_statement_model import IncomeStatementModel
from app.models.fundamentals.cash_flow_model import CashFlowStatementModel
from app.models.fundamentals.balance_sheet_model import BalanceSheetModel


@dataclass
class FundamentalSnapshotModel:
    """ 
    Consolidated, read-optimized snapshot of a company's fundamental data for a given fiscal year.
    """
    # Identification
    symbol: str
    period: str
    fiscal_year: int

    # Full statements (compositon)
    income_statement : Optional[IncomeStatementModel]
    cash_flow_statement : Optional[CashFlowStatementModel]
    balance_sheet : Optional[BalanceSheetModel]

    # Key Metrics (flattened for quick access)
    # From Income Sheet Model
    total_revenue: Optional[float] = None
    net_income:Optional[float] = None
    eps:Optional[float] = None
    # From Cash Flow Model
    operating_cash_flow : Optional[float] = None
    # From Balance Sheet Model 
    total_liabilities : Optional[float] = None
    total_assets : Optional[float] = None
    shareholders_equity : Optional[float] = None