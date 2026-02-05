from dataclasses import dataclass
from app.core.exceptions import ValidationError
from typing import Optional,Literal

periodType = Literal["annual","quarterly"]

@dataclass
class IncomeStatementModel:
  symbol:str
  period:periodType
  fiscal_year:int
  total_revenue: Optional[float] = None
  operating_income:Optional[float] = None
  net_income:Optional[float] = None
  eps:Optional[float] = None

  def __post_init__(self):
    if self.fiscal_year < 1900 :
      raise ValidationError(
        code = "INVALID_YEAR",
        message = "The FISCAL YEAR SHOULD BE GREATER THAN 1900",
        details = {"received" :f"{self.fiscal_year}"}
      )