from typing import Optional,Literal
from dataclasses import dataclass
from datetime import date

periodType = Literal["annual","quarterly"]
@dataclass
class BalanceSheetModel:
  """ 
  Represents the balance sheet data for a company for a fiscal year.
  """
  # Identification
  symbol : str
  period : periodType
  fiscal_year : int
  filing_date : date
  # Assets
  total_assets : Optional[float] = None
  current_assets : Optional[float] = None
  cash_and_equivalents : Optional[float]=None
  #Liabilities 
  total_liabilities : Optional[float] = None
  current_liabilities : Optional[float] = None
  long_term_debt : Optional[float] = None
  # Equity
  shareholders_equity : Optional[float] = None