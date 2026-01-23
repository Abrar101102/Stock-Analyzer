from typing import Optional
from dataclasses import dataclass

@dataclass
class BalanceSheetModel:
  """ 
  Represents the balance sheet data for a company for a fiscal year.
  """
  # Identification
  symbol : str
  period : str
  fiscal_year : int
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