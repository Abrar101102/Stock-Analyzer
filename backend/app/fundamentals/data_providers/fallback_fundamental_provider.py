from typing import List
import logging

from app.fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from app.fundamentals.data_providers.yahoo_fundamental_provider import YahooFundamentalProvider
from app.fundamentals.data_providers.alpha_vantage_provider import AlphaVantageProvider
from app.fundamentals.models.balance_sheet_model import BalanceSheetModel
from app.fundamentals.models.income_statement_model import IncomeStatementModel
from app.fundamentals.models.cash_flow_model import CashFlowStatementModel
from app.registry.symbol_resolver import SymbolResolver
from app.fundamentals.data_providers.screener_provider import ScreenerFundamentalProvider

logger = logging.getLogger(__name__)

# Map provider class → provider name for symbol resolution
PROVIDER_NAME_MAP = {
    AlphaVantageProvider: "alpha_vantage",
    YahooFundamentalProvider: "yahoo",
}


class FallbackFundamentalProvider(BaseFundamentalProvider):
    """
    Tries providers in order and falls back when a provider fails or returns no data.
    Default order: Alpha Vantage -> Yahoo.
    """
    def __init__(self, providers: List[BaseFundamentalProvider] | None = None):
        self.providers = providers or [
            ScreenerFundamentalProvider(), # Fallback: comprehensive scraping
            YahooFundamentalProvider(),     # Primary: fast API
             
        ]

    def _invoke_provider(self, provider: BaseFundamentalProvider, method_name: str, symbol: str, period: str, limit: int):
        method = getattr(provider, method_name)
        try:
            return method(symbol, period, limit)
        except TypeError:
            # Backward compatibility for providers that don't expose `limit` yet.
            return method(symbol, period)

    def _fetch_with_fallback(self, method_name: str, symbol: str, period: str, limit: int):
        last_error = None

        for provider in self.providers:
            provider_name = provider.__class__.__name__
            try:
                records = self._invoke_provider(provider, method_name, symbol, period, limit)
                if records:
                    logger.info(
                        "Fundamental provider succeeded",
                        extra={
                            "provider": provider_name,
                            "method": method_name,
                            "symbol": symbol,
                            "period": period,
                            "count": len(records),
                        },
                    )
                    return records

                logger.warning(
                    "Fundamental provider returned empty data",
                    extra={
                        "provider": provider_name,
                        "method": method_name,
                        "symbol": symbol,
                        "period": period,
                    },
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Fundamental provider failed, trying fallback",
                    extra={
                        "provider": provider_name,
                        "method": method_name,
                        "symbol": symbol,
                        "period": period,
                        "error": str(exc),
                    },
                )

        if last_error is not None:
            raise last_error

        return []

    def get_income_statements(self, symbol: str, period: str = "annual", limit: int = 5) -> List[IncomeStatementModel]:
        return self._fetch_with_fallback("get_income_statements", symbol, period, limit)

    def get_balance_sheets(self, symbol: str, period: str = "annual", limit: int = 5) -> List[BalanceSheetModel]:
        return self._fetch_with_fallback("get_balance_sheets", symbol, period, limit)

    def get_cash_flows(self, symbol: str, period: str = "annual", limit: int = 5) -> List[CashFlowStatementModel]:
        return self._fetch_with_fallback("get_cash_flows", symbol, period, limit)