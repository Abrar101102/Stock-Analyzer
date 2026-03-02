from dataclasses import dataclass
from typing import Optional

@dataclass
class QuarterlyMetricBlock:
  ttm:Optional[float]
  qoq_growth:Optional[float]
  yoy_growth:Optional[float]
  acceleration:Optional[float]

@dataclass
class quarterlyTrendResponse:
  symbol:str
  revenue:QuarterlyMetricBlock
  eps:QuarterlyMetricBlock
  ebitda:QuarterlyMetricBlock