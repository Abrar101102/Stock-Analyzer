from typing import Optional
from dataclasses import dataclass

@dataclass
class StockSymbol:
  symbol:str               #RELIANCE
  exchange:str             #NSE/BSE
  yahoo_symbol:str         #RELIANCE.NS  
  name:Optional[str]=None  #Reliance Industries Limited
  sector:Optional[str]=None#Energy