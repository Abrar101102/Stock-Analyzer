from app.fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from app.fundamentals.models.balance_sheet_model import BalanceSheetModel
from app.fundamentals.models.income_statement_model import IncomeStatementModel
from app.fundamentals.models.cash_flow_model import CashFlowStatementModel

from datetime import date
import yfinance as yf
from typing import List
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class YahooFundamentalProvider(BaseFundamentalProvider):
    """
    Yahoo Finance Fundamental Provider

    Provider responsibilities:
    - Fetch raw data
    - Convert rows → models
    - NO filtering
    - NO limits
    - NO assumptions about ordering
    """

    # ---------- INTERNAL HELPERS ----------

    @staticmethod
    def _get(df: pd.DataFrame, row: str, col) -> float | None:
        """
        Safe row-index lookup for Yahoo Finance dataframes
        """
        if df is None or df.empty:
            return None
        if row not in df.index:
            return None
        # print(df)
        val = df.loc[row, col]
        return None if pd.isna(val) else float(val)

    @staticmethod
    def _year(col) -> int:
        """
        Extract fiscal year from column (Timestamp or int)
        """
        return col.year if hasattr(col, "year") else int(col)
    
    def get_ticker_and_earning(self,symbol):
        ticker = yf.Ticker(symbol)
        earnings_df = ticker.get_earnings_dates(limit=8)
        earnings_map = {}

        if earnings_df is not None and not earnings_df.empty:
            # print("Earnings DF",earnings_df)
            for dt in earnings_df.index:
                # Todo: Improve fiscal year mapping logic
                fy = dt.year - 1
                earnings_map[fy] = dt.date()
        return ticker,earnings_map
    # ---------- BALANCE SHEET ----------

    def get_balance_sheets(self, symbol: str, period: str = "annual") -> List[BalanceSheetModel]:
        ticker,earnings_map = self.get_ticker_and_earning(symbol)
        df = ticker.balance_sheet

        models: List[BalanceSheetModel] = []

        if df is None or df.empty:
            logger.warning(
                "Yahoo returned empty balance sheet",
                extra={"symbol": symbol}
            )
            return models

        logger.debug(f"Raw balance sheet rows: {list(df.index)}")
        
        for col in df.columns:
            
            logger.debug(
            "Parsed balance sheet year",
            extra={"symbol": symbol, "fiscal_year": self._year(col)}
        )
            fy = self._year(col)
            effective_date = earnings_map.get(fy,date.today())
            print(f"filing date {effective_date}")
            models.append(
                BalanceSheetModel(
                    symbol=symbol,
                    period=period,
                    fiscal_year=self._year(col),
                    effective_date= effective_date,
                    total_assets=self._get(df, "Total Assets", col),
                    current_assets=self._get(df, "Current Assets", col),
                    cash_and_equivalents=self._get(df, "Cash And Cash Equivalents", col),
                    total_liabilities=self._get(
                        df, "Total Liabilities Net Minority Interest", col
                    ),
                    current_liabilities=self._get(df, "Current Liabilities", col),
                    long_term_debt=self._get(df, "Total Debt", col),
                    shareholders_equity=self._get(df, "Tangible Book Value", col),
                )
            )

        return models

    # ---------- INCOME STATEMENT ----------

    def get_income_statements(self, symbol: str, period: str = "annual") -> List[IncomeStatementModel]:
        ticker,earnings_map = self.get_ticker_and_earning(symbol)
        df = ticker.financials

        models: List[IncomeStatementModel] = []

        if df is None or df.empty:
            logger.warning(
                "Yahoo returned empty Income sheet",
                extra={"symbol": symbol}
            )
            return models

        logger.debug(f"Raw income statement rows: {list(df.index)}")
       

        for col in df.columns:
            logger.debug(
            "Parsed Income sheet year",
            extra={"symbol": symbol, "fiscal_year": self._year(col)}
        )
            fy = self._year(col)
            effective_date = earnings_map.get(fy,date.today())
            models.append(
                IncomeStatementModel(
                    symbol=symbol,
                    period=period,
                    fiscal_year=self._year(col),
                    effective_date=effective_date,
                    total_revenue=self._get(df, "Total Revenue", col),
                    operating_income=self._get(df, "Operating Income", col),
                    net_income=self._get(df, "Net Income", col),
                    eps=self._get(df, "Basic EPS", col),
                )
            )

        return models

    # ---------- CASH FLOW ----------

    def get_cash_flows(self, symbol: str, period: str = "annual") -> List[CashFlowStatementModel]:
        ticker,earnings_map = self.get_ticker_and_earning(symbol)
        df = ticker.cashflow

        models: List[CashFlowStatementModel] = []

        if df is None or df.empty:
            logger.warning(
                "Yahoo returned empty Cash flows",
                extra={"symbol": symbol}
            )
            return models

        logger.debug(f"Raw cash flow rows: {list(df.index)}")
        

        for col in df.columns:
            logger.debug(
            "Parsed Cash Flow year",
            extra={"symbol": symbol, "fiscal_year": self._year(col)}
        )
            fy = self._year(col)
            effective_date = earnings_map.get(fy,date.today())
            models.append(
                CashFlowStatementModel(
                    symbol=symbol,
                    period=period,
                    fiscal_year=self._year(col),
                    effective_date=effective_date,
                    operating_cash_flow=self._get(df, "Operating Cash Flow", col),
                    capital_expenditure=self._get(df, "Capital Expenditure", col),
                    net_cash_flow=self._get(df, "Free Cash Flow", col),
                    investing_cash_flow=self._get(
                        df, "Total Cash Flows From Investing Activities", col
                    ),
                    financing_cash_flow=self._get(
                        df, "Total Cash From Financing Activities", col
                    ),
                )
            )

        return models
    def get_available_years(self, symbol: str) -> List[int]:
        ticker, _ = self.get_ticker_and_earning(symbol)
        balance_sheet_df = ticker.balance_sheet
        if balance_sheet_df is None or balance_sheet_df.empty:
            return []
        return [self._year(col) for col in balance_sheet_df.columns]