from dataclasses import dataclass
from typing import Optional

@dataclass
class ValuationResponse:
  symbol:str
  price:float
  market_cap:Optional[float]
  pe_ratio:Optional[float]
  ev:Optional[float]
  ev_ebitda:Optional[float]
  price_to_book:Optional[float]
  