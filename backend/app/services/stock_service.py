from typing import Dict,List
from app.registry.stock_registry import StockRegistry
from app.data_providers.base_provider import MarketDataProvider
from app.data_sources.market_data_source import MarketDataSource
from app.core.exceptions import NotFoundError

class StockService:
  """
  Service class for stock-related operations.
  """
  def __init__(self,provider:MarketDataProvider):
    self.provider = provider

  def get_price_history(self,symbol:str,period:str="6mo")->List[Dict]:
    if not StockRegistry.exists(symbol):
      raise NotFoundError(
        code = "INVALID_SYMBOL",
        message = "ENTERED STOCK SYMBOL IS NOT IN REGISTRY",
        details = {"received":f"Stock symbol {symbol} not found in registry."}
      )
    
    stock = StockRegistry.get_stock(symbol)

    return self.provider.get_price_history(stock.yahoo_symbol,period)