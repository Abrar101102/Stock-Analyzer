from typing import Optional
from dataclasses import dataclass

@dataclass
class StockSymbol:
  symbol:str               #RELIANCE
  exchange:str             #NSE/BSE
  yahoo_symbol:str         #RELIANCE.NS  
  name:Optional[str]=None  #Reliance Industries Limited
  sector:Optional[str]=None#Energy
  alpha_vantage_symbol: str = ""

  def get_symbol_for(self, provider: str) -> str:
    """
    Returns the correct symbol format for a given provider.
    
    Provider → Format mapping:
      yahoo           → RELIANCE.NS
      alpha_vantage   → RELIANCE.BSE
      default         → canonical symbol (RELIANCE)
    """
    mapping = {
      "yahoo": self.yahoo_symbol,
      "alpha_vantage": self.alpha_vantage_symbol or self.yahoo_symbol,
    }
    return mapping.get(provider, self.symbol)