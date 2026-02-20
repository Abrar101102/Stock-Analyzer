from dataclasses import dataclass
from typing import List,Optional

@dataclass
class YearTrend:
  fiscal_year:int
  revenue:Optional[float]
  revenue_growth:Optional[float]
  net_income:Optional[float]
  net_income_growth:Optional[float]
  roe:Optional[float]

@dataclass
class TrendResponse:
  symbol:str
  years:List[YearTrend]
  
