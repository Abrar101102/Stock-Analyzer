from app.fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from app.fundamentals.models.balance_sheet_model import BalanceSheetModel
from app.fundamentals.models.income_statement_model import IncomeStatementModel
from app.fundamentals.models.cash_flow_model import CashFlowStatementModel
from app.core.config import ALPHA_VANTAGE_API_KEY

from datetime import date
import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Alpha Vantage API base URL
ALPHA_VANTAGE_BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageProvider(BaseFundamentalProvider):
    """
    Alpha Vantage Fundamental Data Provider

    Provider responsibilities:
    - Fetch raw data from Alpha Vantage API
    - Convert JSON responses → models
    - NO filtering
    - NO limits
    - NO assumptions about ordering
    """

    def __init__(self):
        self.api_key = ALPHA_VANTAGE_API_KEY
        self.base_url = ALPHA_VANTAGE_BASE_URL

    # ---------- INTERNAL HELPERS ----------

    def _make_request(self, function: str, symbol: str) -> Optional[Dict]:
        """
        Make HTTP request to Alpha Vantage API
        """
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check for API errors
            if "Error Message" in data:
                logger.warning(
                    f"Alpha Vantage API error for {symbol}: {data['Error Message']}"
                )
                return None

            if "Note" in data:
                logger.warning(
                    f"Alpha Vantage API rate limit for {symbol}: {data['Note']}"
                )
                return None

            return data
        except requests.exceptions.RequestException as e:
            logger.error(
                f"Failed to fetch {function} for {symbol}",
                extra={"symbol": symbol, "function": function, "error": str(e)},
            )
            return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """
        Safe conversion to float, handles None and string values
        """
        if value is None:
            return None
        if isinstance(value, str):
            if value.strip() == "":
                return None
            try:
                return float(value)
            except ValueError:
                return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_year(date_str: str) -> Optional[int]:
        """
        Extract fiscal year from ISO date string (YYYY-MM-DD)
        """
        if not date_str:
            return None
        try:
            return int(date_str[:4])
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _parse_date(date_str: str) -> date:
        """
        Parse ISO date string to date object
        """
        if not date_str:
            return date.today()
        try:
            parts = date_str.split("-")
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        except (ValueError, IndexError):
            return date.today()

    # ---------- BALANCE SHEET ----------

    def get_balance_sheets(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[BalanceSheetModel]:
        """
        Fetch balance sheet data from Alpha Vantage
        """
        data = self._make_request("BALANCE_SHEET", symbol)

        if not data:
            logger.warning(
                "Alpha Vantage returned no balance sheet data",
                extra={"symbol": symbol},
            )
            return []

        models: List[BalanceSheetModel] = []

        # Determine which key to use based on period
        if period == "annual":
            reports_key = "annualReports"
        elif period == "quarter":
            reports_key = "quarterlyReports"
        else:
            logger.warning(f"Invalid period {period}", extra={"symbol": symbol})
            return models

        reports = data.get(reports_key, [])

        if not reports:
            logger.warning(
                f"No {period} balance sheet reports for {symbol}",
                extra={"symbol": symbol},
            )
            return models

        for report in reports[:limit]:
            try:
                fiscal_year = self._extract_year(report.get("fiscalDateEnding"))
                if not fiscal_year:
                    continue

                fiscal_quarter = None
                if period == "quarter":
                    # Parse quarter from fiscalDateEnding if possible
                    fiscal_date = self._parse_date(report.get("fiscalDateEnding"))
                    fiscal_quarter = (fiscal_date.month - 1) // 3 + 1

                logger.debug(
                    "Parsed balance sheet",
                    extra={"symbol": symbol, "fiscal_year": fiscal_year},
                )

                models.append(
                    BalanceSheetModel(
                        symbol=symbol,
                        period=period,
                        fiscal_year=fiscal_year,
                        fiscal_quarter=fiscal_quarter,
                        effective_date=self._parse_date(
                            report.get("fiscalDateEnding")
                        ),
                        total_assets=self._safe_float(report.get("totalAssets")),
                        current_assets=self._safe_float(report.get("totalCurrentAssets")),
                        cash_and_equivalents=self._safe_float(
                            report.get("cashAndCashEquivalentsAtCarryingValue")
                        ),
                        total_liabilities=self._safe_float(
                            report.get("totalLiabilities")
                        ),
                        current_liabilities=self._safe_float(
                            report.get("totalCurrentLiabilities")
                        ),
                        long_term_debt=self._safe_float(report.get("longTermDebt")),
                        shareholders_equity=self._safe_float(
                            report.get("totalShareholderEquity")
                        ),
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to parse balance sheet report for {symbol}: {str(e)}",
                    extra={"symbol": symbol},
                )
                continue

        return models

    # ---------- INCOME STATEMENT ----------

    def get_income_statements(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[IncomeStatementModel]:
        """
        Fetch income statement data from Alpha Vantage
        """
        data = self._make_request("INCOME_STATEMENT", symbol)

        if not data:
            logger.warning(
                "Alpha Vantage returned no income statement data",
                extra={"symbol": symbol},
            )
            return []

        models: List[IncomeStatementModel] = []

        # Determine which key to use based on period
        if period == "annual":
            reports_key = "annualReports"
        elif period == "quarter":
            reports_key = "quarterlyReports"
        else:
            logger.warning(f"Invalid period {period}", extra={"symbol": symbol})
            return models

        reports = data.get(reports_key, [])

        if not reports:
            logger.warning(
                f"No {period} income statement reports for {symbol}",
                extra={"symbol": symbol},
            )
            return models

        for report in reports[:limit]:
            try:
                fiscal_year = self._extract_year(report.get("fiscalDateEnding"))
                if not fiscal_year:
                    continue

                fiscal_quarter = None
                if period == "quarter":
                    # Parse quarter from fiscalDateEnding if possible
                    fiscal_date = self._parse_date(report.get("fiscalDateEnding"))
                    fiscal_quarter = (fiscal_date.month - 1) // 3 + 1

                logger.debug(
                    "Parsed income statement",
                    extra={"symbol": symbol, "fiscal_year": fiscal_year},
                )

                models.append(
                    IncomeStatementModel(
                        symbol=symbol,
                        period=period,
                        fiscal_year=fiscal_year,
                        fiscal_quarter=fiscal_quarter,
                        effective_date=self._parse_date(
                            report.get("fiscalDateEnding")
                        ),
                        total_revenue=self._safe_float(report.get("totalRevenue")),
                        operating_income=self._safe_float(
                            report.get("operatingIncome")
                        ),
                        net_income=self._safe_float(report.get("netIncome")),
                        eps=self._safe_float(report.get("basicEPS")),
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to parse income statement report for {symbol}: {str(e)}",
                    extra={"symbol": symbol},
                )
                continue

        return models

    # ---------- CASH FLOW ----------

    def get_cash_flows(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[CashFlowStatementModel]:
        """
        Fetch cash flow statement data from Alpha Vantage
        """
        data = self._make_request("CASH_FLOW", symbol)

        if not data:
            logger.warning(
                "Alpha Vantage returned no cash flow data",
                extra={"symbol": symbol},
            )
            return []

        models: List[CashFlowStatementModel] = []

        # Determine which key to use based on period
        if period == "annual":
            reports_key = "annualReports"
        elif period == "quarter":
            reports_key = "quarterlyReports"
        else:
            logger.warning(f"Invalid period {period}", extra={"symbol": symbol})
            return models

        reports = data.get(reports_key, [])

        if not reports:
            logger.warning(
                f"No {period} cash flow reports for {symbol}",
                extra={"symbol": symbol},
            )
            return models

        for report in reports[:limit]:
            try:
                fiscal_year = self._extract_year(report.get("fiscalDateEnding"))
                if not fiscal_year:
                    continue

                fiscal_quarter = None
                if period == "quarter":
                    # Parse quarter from fiscalDateEnding if possible
                    fiscal_date = self._parse_date(report.get("fiscalDateEnding"))
                    fiscal_quarter = (fiscal_date.month - 1) // 3 + 1

                logger.debug(
                    "Parsed cash flow statement",
                    extra={"symbol": symbol, "fiscal_year": fiscal_year},
                )

                models.append(
                    CashFlowStatementModel(
                        symbol=symbol,
                        period=period,
                        fiscal_year=fiscal_year,
                        fiscal_quarter=fiscal_quarter,
                        effective_date=self._parse_date(
                            report.get("fiscalDateEnding")
                        ),
                        operating_cash_flow=self._safe_float(
                            report.get("operatingCashflow")
                        ),
                        capital_expenditure=self._safe_float(
                            report.get("capitalExpenditures")
                        ),
                        investing_cash_flow=self._safe_float(
                            report.get("cashflowFromInvestment")
                        ),
                        financing_cash_flow=self._safe_float(
                            report.get("cashflowFromFinancing")
                        ),
                        net_cash_flow=self._safe_float(report.get("changeInCash")),
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to parse cash flow report for {symbol}: {str(e)}",
                    extra={"symbol": symbol},
                )
                continue

        return models
