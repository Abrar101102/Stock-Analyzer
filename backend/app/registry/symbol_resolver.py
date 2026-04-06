from app.registry.stock_registry import StockRegistry
from app.core.exceptions import NotFoundError
from sqlalchemy.orm import Session
import logging

logger = logging.getLogger(__name__)


class SymbolResolver:
  """
  Translates a canonical symbol (e.g., "RELIANCE") into the
  provider-specific format each API expects.
  
  Call flow:
    User → "RELIANCE" → SymbolResolver.resolve("RELIANCE", "alpha_vantage")
                          → returns "RELIANCE.BSE"
    User → "RELIANCE" → SymbolResolver.resolve("RELIANCE", "yahoo")
                          → returns "RELIANCE.NS"

  This replaces the old _normalize_symbol() that hardcoded yahoo_symbol.
  """

  @staticmethod
  def resolve(symbol: str, provider: str, db: Session | None = None) -> str:
    """
    Resolve a canonical symbol to the provider-specific format.
    
    :param symbol: Canonical symbol (e.g. "RELIANCE") or already-resolved symbol
    :param provider: Provider name ("yahoo", "alpha_vantage")
    :return: Provider-specific symbol string
    """
    normalized = symbol.upper().strip()

    # If a request-scoped DB session is provided and the registry knows
    # this symbol, use the provider-specific mapping.
    if db and StockRegistry.exists(normalized, db):
      stock = StockRegistry.get_stock(normalized, db)
      resolved = stock.get_symbol_for(provider)
      logger.debug(
        "Resolved symbol from registry",
        extra={
          "canonical": normalized,
          "provider": provider,
          "resolved": resolved
        }
      )
      return resolved

    # If it's already in provider format (e.g., "RELIANCE.NS"), pass through
    # This handles cases where the symbol was already resolved upstream
    logger.debug(
      f"Symbol not in registry, passing through as-is",
      extra={"symbol": normalized, "provider": provider}
    )
    return normalized

  @staticmethod
  def resolve_strict(symbol: str, provider: str, db: Session) -> str:
    """Same as resolve() but raises if symbol not in registry."""
    normalized = symbol.upper().strip()
    stock = StockRegistry.get_stock(normalized, db)  # raises NotFoundError
    return stock.get_symbol_for(provider)