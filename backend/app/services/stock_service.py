from typing import Dict,List
from app.registry.stock_registry import StockRegistry
from app.data_providers.base_provider import MarketDataProvider
from app.data_sources.market_data_source import MarketDataSource
from app.registry.symbol_resolver import SymbolResolver
from app.core.exceptions import NotFoundError
from app.db.session import SessionLocal

# Map provider class → provider name for symbol resolution
PROVIDER_NAME_MAP = {
    "YahooMarketDataProvider": "yahoo",
    "AlphaVantageProvider": "alpha_vantage",
}

db = SessionLocal()

class StockService:
  """
  Service class for stock-related operations.
  """
  def __init__(self,provider:MarketDataProvider):
    self.provider = provider
    self._provider_name = PROVIDER_NAME_MAP.get(
      provider.__class__.__name__, "yahoo"
    )

  def get_price_history(self,symbol:str,period:str="6mo")->List[Dict]:
    if not StockRegistry.exists(symbol,db):
      raise NotFoundError(
        code = "INVALID_SYMBOL",
        message = "ENTERED STOCK SYMBOL IS NOT IN REGISTRY",
        details = {"received":f"Stock symbol {symbol} not found in registry."}
      )
    
    # Resolve to the correct format for THIS provider
    resolved = SymbolResolver.resolve(symbol, self._provider_name)
    print("Resolved symbol for provider", self._provider_name, ":", resolved)
    return self.provider.get_price_history(resolved,period)