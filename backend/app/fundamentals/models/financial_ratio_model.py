from dataclasses import dataclass
from typing import Optional

@dataclass
class FinancialRatioModel:
  """
  Represents key financial ratios for a company for a fiscal year.
  """
  symbol : str
  fiscal_year : int
  fiscal_quarter:Optional[int]=None
  net_margin : Optional[float] = None
  current_ratio : Optional[float] = None
  debt_to_equity : Optional[float] = None
  ocf_quality : Optional[float] = None
  free_cash_flow : Optional[float] = None