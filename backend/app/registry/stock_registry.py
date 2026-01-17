from typing import Dict
from app.models.stock import StockSymbol

class StockRegistry:
  """
  Central Registry of Supported Stocks.
  Act as a single source of truth for stock meta data
  """
  _stocks: Dict[str,StockSymbol] = {
    "RELIANCE": StockSymbol(
      symbol="RELIANCE",
      exchange="NSE",
      yahoo_symbol="RELIANCE.NS",
      name="Reliance Industries Limited",
      sector="Energy"
    ),
    "TCS": StockSymbol(
      symbol="TCS",
      exchange="NSE",
      yahoo_symbol="TCS.NS",
      name="Tata Consultancy Services Limited",
      sector="IT"
    ),
    
  }
  @classmethod
  def get(cls,symbol)->  StockSymbol:
    normalized = symbol.upper()
    return cls._stocks[normalized]
  
  @classmethod
  def exists(cls,symbol) -> bool:
    return symbol.upper() in cls._stocks
  
  @classmethod
  def list_all(cls):
    return cls._stocks.copy()
