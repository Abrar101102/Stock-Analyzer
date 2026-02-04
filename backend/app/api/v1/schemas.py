from dataclasses import dataclass
from typing import Optional

@dataclass
class FundamentalSnapshotV1:
  symbol: str
  fiscal_year :int
  period:int

  total_revenue:Optional[float]=None
  net_income:Optional[float]=None
  eps:Optional[float]=None

  operational_cash_flow : Optional[float] = None

  total_assets:Optional[float]=None
  total_liabilities:Optional[float] = None
  shareholers_equity:Optional[float]=None

@dataclass
class IncomeStatementV1:
  symbol: str
  fiscal_year :int
  period:int
  total_revenue: Optional[float] = None
  operating_income:Optional[float] = None
  net_income:Optional[float] = None
  eps:Optional[float] = None

@dataclass
class BalanceSheetV1:
  symbol: str
  fiscal_year :int
  period:int
  total_assets : Optional[float] = None
  current_assets : Optional[float] = None
  cash_and_equivalents : Optional[float]=None
  #Liabilities 
  total_liabilities : Optional[float] = None
  current_liabilities : Optional[float] = None
  long_term_debt : Optional[float] = None
  # Equity
  shareholders_equity : Optional[float] = None

@dataclass
class CashFlowV1:
  symbol: str
  fiscal_year :int
  period:int
   # operating cash flow
  operating_cash_flow : Optional[float] = None
  # Investing Cash Flow
  capital_expenditure : Optional[float] = None
  investing_cash_flow : Optional[float] = None
  # Financing Cash Flow
  financing_cash_flow : Optional[float] = None
  # Net Result
  net_cash_flow : Optional[float] = None

@dataclass
class RatioV1:
  symbol : str
  fiscal_year : int
  net_margin : Optional[float] = None
  current_ratio : Optional[float] = None
  debt_to_equity : Optional[float] = None
  ocf_quality : Optional[float] = None
  free_cash_flow : Optional[float] = None