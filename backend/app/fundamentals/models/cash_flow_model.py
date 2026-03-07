from dataclasses import dataclass
from typing import Optional,Literal
from datetime import date

periodType = Literal["annual","quarter"]

@dataclass
class CashFlowStatementModel:
  """
  Represents a company's cash flow statement for a specific fiscal period.
  """
  symbol:str
  period:periodType
  fiscal_year:int
  
  effective_date:date
  fiscal_quarter:Optional[int]=None
  # operating cash flow
  operating_cash_flow : Optional[float] = None
  # Investing Cash Flow
  capital_expenditure : Optional[float] = None
  investing_cash_flow : Optional[float] = None
  # Financing Cash Flow
  financing_cash_flow : Optional[float] = None
  # Net Result
  net_cash_flow : Optional[float] = None