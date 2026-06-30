from typing import Dict, List
from sqlalchemy.orm import Session
from app.registry.stock_registry import StockRegistry
from app.data_providers.base_provider import MarketDataProvider
from app.registry.symbol_resolver import SymbolResolver
from app.core.exceptions import NotFoundError
from app.core.logging import trace
import logging

# Map provider class → provider name for symbol resolution
PROVIDER_NAME_MAP = {
    "YahooMarketDataProvider": "yahoo",
    "AlphaVantageProvider": "alpha_vantage",
}

logger = logging.getLogger(__name__)

class StockService:
  """
  Service class for stock-related operations.
  """
  def __init__(self, provider: MarketDataProvider, db: Session):
    self.provider = provider
    self.db = db
    self._provider_name = PROVIDER_NAME_MAP.get(
      provider.__class__.__name__, "yahoo"
    )

  def _canonical_symbol(self, symbol: str) -> str:
    return symbol.upper().strip().split(".")[0]

  @trace
  def _register_symbol_if_missing(self, symbol: str):
    canonical = self._canonical_symbol(symbol)
    if StockRegistry.exists(canonical, self.db):
      return

    exchange = "BSE" if symbol.upper().endswith(".BO") else "NSE"
    StockRegistry.add_stock(
      db=self.db,
      symbol=canonical,
      name=canonical,
      exchange=exchange,
      is_nifty50=False,
      is_nifty500=False,
    )
    logger.info("Auto-registered symbol after provider success", extra={"symbol": canonical})

  @trace
  def _provider_candidates(self, symbol: str) -> List[str]:
    normalized = symbol.upper().strip()
    candidates = [normalized]
    if "." not in normalized and self._provider_name == "yahoo":
      candidates.append(f"{normalized}.NS")
      candidates.append(f"{normalized}.BO")
    return candidates

  @trace
  def _fetch_with_fallback(self, symbol: str, period: str) -> List[Dict]:
    errors: List[str] = []
    for candidate in self._provider_candidates(symbol):
      try:
        data = self.provider.get_price_history(candidate, period)
        if data:
          self._register_symbol_if_missing(symbol)
          return data
      except Exception as exc:
        errors.append(f"{candidate}: {exc}")

    raise NotFoundError(
      code="INVALID_SYMBOL",
      message="ENTERED STOCK SYMBOL IS INVALID OR NOT AVAILABLE",
      details={"received": symbol, "attempts": errors},
    )

  @trace
  def get_price_history(self,symbol:str,period:str="6mo")->List[Dict]:
    normalized = symbol.upper().strip()
    if not StockRegistry.exists(normalized, self.db):
      logger.warning("Symbol not in registry, trying provider fallback", extra={"symbol": normalized})
      return self._fetch_with_fallback(normalized, period)

    resolved = SymbolResolver.resolve(normalized, self._provider_name, self.db)
    data = self.provider.get_price_history(resolved, period)
    if data:
      return data

    logger.warning("Registry-resolved symbol returned empty data, trying fallback", extra={"symbol": normalized})
    return self._fetch_with_fallback(normalized, period)