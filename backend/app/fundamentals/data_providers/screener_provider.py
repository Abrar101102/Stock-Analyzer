from app.fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from app.fundamentals.models.balance_sheet_model import BalanceSheetModel
from app.fundamentals.models.income_statement_model import IncomeStatementModel
from app.fundamentals.models.cash_flow_model import CashFlowStatementModel

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date
from typing import List, Dict, Optional
import logging
import time
import re
import random

logger = logging.getLogger(__name__)


class ScreenerFundamentalProvider(BaseFundamentalProvider):
    """
    Screener.in Fundamental Data Provider (Web Scraping)

    Scrapes https://www.screener.in/company/{SYMBOL}/consolidated/
    Parses structured HTML tables into your existing models.

    IMPORTANT:
    - Rate-limit yourself (1 request per 2 seconds minimum)
    - Cache aggressively — fundamentals don't change often
    - For personal/educational use only
    """

    BASE_URL = "https://www.screener.in/company"

    # In-memory cache: {symbol: {section_name: DataFrame}}
    _cache: Dict[str, Dict[str, pd.DataFrame]] = {}
    _cache_timestamps: Dict[str, float] = {}
    CACHE_TTL = 3600  # 1 hour — fundamentals don't change intraday
    last_request_ts: float = 0.0
    MIN_DELAY_SECONDS = 3.0  # be conservative

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })

    def _wait_for_slot(self):
        now = time.time()
        elapsed = now - self._last_request_ts
        if elapsed < self.MIN_DELAY_SECONDS:
            time.sleep((self.MIN_DELAY_SECONDS - elapsed) + random.uniform(0.2, 0.8))
        self._last_request_ts = time.time()

    def _fetch_url(self, url: str):
        self._wait_for_slot()

        resp = self.session.get(url, timeout=15)

        # Backoff on 429
        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            base = float(retry_after) if retry_after else 30.0
            sleep_for = base + random.uniform(1.0, 3.0)
            logger.warning(f"Screener 429. Backing off for {sleep_for:.1f}s", extra={"url": url})
            time.sleep(sleep_for)
            return None

        return resp
    

    # ══════════════════════════════════════
    #  INTERNAL: SCRAPING & PARSING
    # ══════════════════════════════════════

    from app.core.cache import redis_cache

    @redis_cache(expire_seconds=86400)
    def _fetch_html(self, url: str) -> Optional[str]:
        try:
            logger.info(f"Scraping screener.in: {url}")
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                time.sleep(1.5)  # Rate limiting
                return response.text
            elif response.status_code == 404:
                return None
            else:
                logger.warning(f"Screener returned {response.status_code} for {url}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch screener page: {e}")
            return None

    def _fetch_page(self, symbol: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse the screener.in company page.
        Uses /consolidated/ for companies with subsidiaries.
        Falls back to standalone if consolidated 404s.
        """
        # Check cache
        if symbol in self._cache:
            age = time.time() - self._cache_timestamps.get(symbol, 0)
            if age < self.CACHE_TTL:
                logger.debug(f"Returning cached screener data for {symbol}")
                return None  # Signal to use cache

        for suffix in ["/consolidated/", "/"]:
            url = f"{self.BASE_URL}/{symbol}{suffix}"
            html = self._fetch_html(url)
            if html:
                return BeautifulSoup(html, "html.parser")

        return None
    
    # ─────────────────────────────────────────────
    # Sector & Industry Extraction (Robust)
    # ─────────────────────────────────────────────
    def _extract_sector_industry_from_peers(self, soup):
        """
        Extract sector & industry from peers breadcrumb (MOST reliable).
        """
        peers_section = soup.find("section", id="peers")
        if not peers_section:
            return None, None

        sub_block = peers_section.find("p", class_="sub")
        if not sub_block:
            return None, None

        sector = None
        industry = None

        for a in sub_block.find_all("a", href=True):
            title = a.get("title", "").lower()
            text = a.get_text(strip=True)

            if title == "sector":
                sector = text
            elif title == "industry":
                industry = text

        return sector, industry
    
    def get_company_overview(self, symbol: str) -> dict:
        symbol = self._normalize_for_screener(symbol)
        soup = self._fetch_page(symbol)

        sector, industry = self._extract_sector_industry_from_peers(soup)

        if not soup:
            raise ValueError(f"Could not fetch or parse page for {symbol}")

        overview = {
            "symbol": symbol,
            "name": symbol,
            "sector": sector,
            "industry": industry,
            "metrics": {}
        }

        # Company name
        name_tag = soup.find("h1", class_="h2")
        if name_tag:
            overview["name"] = name_tag.text.strip()

        # ── ADD THIS: Sector & Industry from company-info section ──
        company_info = soup.find("div", class_="company-info")
        if company_info:
            for a_tag in company_info.find_all("a"):
                href = a_tag.get("href", "")
                text = a_tag.text.strip()
                if "/industry/" in href:
                    overview["industry"] = text
                elif "/sector/" in href:
                    overview["sector"] = text

        # Fallback: check breadcrumb / sub-links area
        if overview["sector"] == "N/A":
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href", "")
                if "/sector/" in href and a_tag.text.strip():
                    overview["sector"] = a_tag.text.strip()
                    break
        if overview["industry"] == "N/A":
            for a_tag in soup.find_all("a", href=True):
                href = a_tag.get("href", "")
                if "/industry/" in href and a_tag.text.strip():
                    overview["industry"] = a_tag.text.strip()
                    break

        # ... rest of your existing ratios scraping code unchanged ...
        ratios_ul = soup.find("ul", id="top-ratios")
        # (keep everything below this line exactly as before)
        if ratios_ul:
            # Map screener text labels to our API keys
            metric_map = {
                "Market Cap": "market_cap",
                "Current Price": "price",
                "High / Low": "high_low",
                "Stock P/E": "pe_ratio",
                "Dividend Yield": "dividend_yield",
                "ROCE": "roce",
                "ROE": "roe",
                "Debt to equity": "debt_to_equity",
                "Face Value": "face_value"
            }

            for li in ratios_ul.find_all("li"):
                name_span = li.find("span", class_="name")
                value_span = li.find("span", class_="number")
                
                if name_span and value_span:
                    label = name_span.text.strip()
                    val_text = value_span.text.replace(",", "").strip()
                    
                    try:
                        # Convert to float if possible
                        val = float(val_text)
                    except ValueError:
                        val = val_text # Keep as string if it's "150 / 120" (High/Low)

                    # Assign to correct field
                    if label in metric_map:
                        key = metric_map[label]
                        if key == "price":
                            overview["price"] = val
                        elif key == "market_cap":
                            overview["market_cap"] = val
                        else:
                            overview["metrics"][key] = val

        return overview

    def _parse_all_sections(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """
        Parse ALL financial tables from the page into DataFrames.
        Returns: {"Profit & Loss": DataFrame, "Balance Sheet": DataFrame, ...}
        """
        symbol = self._normalize_for_screener(symbol)
        # Return from cache if valid
        if symbol in self._cache:
            age = time.time() - self._cache_timestamps.get(symbol, 0)
            if age < self.CACHE_TTL:
                return self._cache[symbol]

        soup = self._fetch_page(symbol)
        if soup is None and symbol in self._cache:
            return self._cache[symbol]
        if soup is None:
            return {}

        sections: Dict[str, pd.DataFrame] = {}

        # Screener uses <section> tags with specific IDs
        section_map = {
            "profit-loss": "Profit & Loss",
            "balance-sheet": "Balance Sheet",
            "cash-flow": "Cash Flows",
            "quarters": "Quarterly Results",
        }

        for section_id, section_name in section_map.items():
            section_tag = soup.find("section", id=section_id)
            if not section_tag:
                logger.debug(f"Section '{section_id}' not found for {symbol}")
                continue

            table = section_tag.find("table", class_="data-table")
            if not table:
                logger.debug(f"No data-table in section '{section_id}' for {symbol}")
                continue

            try:
                df = self._table_to_dataframe(table)
                if df is not None and not df.empty:
                    sections[section_name] = df
                    logger.debug(
                        f"Parsed '{section_name}' for {symbol}: "
                        f"{len(df)} rows x {len(df.columns)} cols"
                    )
            except Exception as e:
                logger.warning(f"Failed to parse '{section_name}' for {symbol}: {e}")

        # Update cache
        self._cache[symbol] = sections
        self._cache_timestamps[symbol] = time.time()

        return sections

    def _table_to_dataframe(self, table) -> Optional[pd.DataFrame]:
        """Convert a screener HTML table to a pandas DataFrame."""
        rows = table.find_all("tr")
        if not rows:
            return None

        # Header row → column names (years)
        headers = []
        header_row = rows[0]
        for th in header_row.find_all(["th", "td"]):
            text = th.get_text(strip=True)
            headers.append(text)

        # Data rows
        data = []
        for row in rows[1:]:
            cols = row.find_all(["td", "th"])
            row_data = [col.get_text(strip=True) for col in cols]
            if row_data:
                data.append(row_data)

        if not headers or not data:
            return None

        df = pd.DataFrame(data, columns=headers[:len(data[0])])
        return df

    @staticmethod
    def _parse_screener_number(value: str) -> Optional[float]:
        """
        Parse screener.in number format to float.
        Handles: "1,23,456", "1,23,456.78", "-1,234", "", "—"
        Indian number system uses commas: 1,00,000 = 100000
        """
        if not value or value.strip() in ("", "—", "-", "N/A"):
            return None
        cleaned = value.replace(",", "").replace(" ", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _extract_fiscal_year(col_name: str) -> Optional[int]:
        """
        Extract fiscal year from screener column headers.
        "Mar 2025" → 2025, "Dec 2024" → 2025 (FY ending), "TTM" → None
        """
        if not col_name or col_name.strip().upper() == "TTM":
            return None

        match = re.search(r"(\w+)\s+(\d{4})", col_name.strip())
        if not match:
            return None

        month_str = match.group(1)
        year = int(match.group(2))
        return year

    @staticmethod
    def _extract_quarter(col_name: str) -> Optional[int]:
        """
        Extract quarter from screener quarterly column headers.
        "Mar 2025" → 4, "Jun 2025" → 1, "Sep 2024" → 2, "Dec 2024" → 3
        """
        month_map = {
            "mar": 4, "apr": 1, "jun": 1, "jul": 2,
            "sep": 2, "oct": 3, "dec": 3, "jan": 4
        }
        match = re.search(r"(\w+)\s+(\d{4})", col_name.strip())
        if not match:
            return None
        month_str = match.group(1).lower()[:3]
        return month_map.get(month_str)
    @staticmethod
    def _normalize_for_screener(symbol: str) -> str:
        """
        Convert any symbol format to screener.in format.
        
        "RELIANCE.NS"  → "RELIANCE"
        "RELIANCE.BSE" → "RELIANCE"
        "RELIANCE"     → "RELIANCE"
        "TCS.NS"       → "TCS"
        """
        # Strip exchange suffixes
        for suffix in [".NS", ".BSE", ".BO", ".NSE"]:
            if symbol.upper().endswith(suffix):
                return symbol[: -len(suffix)].upper()
        return symbol.upper()

    def _get_row_value(self, df: pd.DataFrame, row_name: str, col: str) -> Optional[float]:
        """
        Lookup a value from the DataFrame by row label and column.
        Handles partial matching for row names.
        """
        if df is None or df.empty:
            return None

        first_col = df.columns[0]  # "Particulars" or similar

        for _, row in df.iterrows():
            cell = str(row[first_col]).strip().lower()
            if row_name.lower() in cell:
                return self._parse_screener_number(str(row[col]))

        return None

    # ══════════════════════════════════════
    #  PUBLIC API: BaseFundamentalProvider
    # ══════════════════════════════════════

    def get_income_statements(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[IncomeStatementModel]:
        symbol = self._normalize_for_screener(symbol)

        sections = self._parse_all_sections(symbol)

        if period == "annual":
            df = sections.get("Profit & Loss")
        elif period == "quarter":
            df = sections.get("Quarterly Results")
        else:
            return []

        if df is None or df.empty:
            logger.warning(f"No income data from screener for {symbol}")
            return []

        models: List[IncomeStatementModel] = []
        year_cols = [c for c in df.columns[1:] if self._extract_fiscal_year(c)]
        year_cols = list(reversed(year_cols))  # ← newest first

        for col in year_cols[:limit]:
            fiscal_year = self._extract_fiscal_year(col)
            if not fiscal_year:
                continue

            fiscal_quarter = self._extract_quarter(col) if period == "quarter" else None

            # Screener row labels for Profit & Loss:
            #   Sales/Revenue, Operating Profit, Net Profit, EPS
            models.append(
                IncomeStatementModel(
                    symbol=symbol,
                    period=period,
                    fiscal_year=fiscal_year,
                    fiscal_quarter=fiscal_quarter,
                    effective_date=date(fiscal_year, 3, 31),  # Indian FY ends March
                    total_revenue=self._get_row_value(df, "sales", col),
                    operating_income=self._get_row_value(df, "operating profit", col),
                    net_income=self._get_row_value(df, "net profit", col),
                    eps=self._get_row_value(df, "eps", col),
                )
            )

        return models

    def get_balance_sheets(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[BalanceSheetModel]:
        symbol = self._normalize_for_screener(symbol)
        sections = self._parse_all_sections(symbol)
        df = sections.get("Balance Sheet")

        if df is None or df.empty:
            logger.warning(f"No balance sheet data from screener for {symbol}")
            return []

        if period == "quarter":
            logger.info("Screener does not provide quarterly balance sheets")
            return []

        models: List[BalanceSheetModel] = []
        year_cols = [c for c in df.columns[1:] if self._extract_fiscal_year(c)]
        year_cols = list(reversed(year_cols))  # newest first

        for col in year_cols[:limit]:
            fiscal_year = self._extract_fiscal_year(col)
            if not fiscal_year:
                continue

            # ─── Parse individual components ───
            equity_capital = self._get_row_value(df, "equity capital", col)
            reserves = self._get_row_value(df, "reserves", col)
            borrowings = self._get_row_value(df, "borrowings", col)
            other_liabilities = self._get_row_value(df, "other liabilities", col)
            total_assets = self._get_row_value(df, "total assets", col)

            # Fixed assets section
            fixed_assets = self._get_row_value(df, "fixed assets", col)
            investments = self._get_row_value(df, "investments", col)
            other_assets = self._get_row_value(df, "other assets", col)

            # ─── Compute derived values ───
            # Shareholders equity = Equity Capital + Reserves
            shareholders_equity = None
            if equity_capital is not None and reserves is not None:
                shareholders_equity = equity_capital + reserves
            elif reserves is not None:
                shareholders_equity = reserves  # reserves alone as fallback

            # True total liabilities = Borrowings + Other Liabilities
            # (NOT screener's "Total Liabilities" which is the balancing figure)
            total_liabilities = None
            if borrowings is not None and other_liabilities is not None:
                total_liabilities = borrowings + other_liabilities
            elif borrowings is not None:
                total_liabilities = borrowings
            elif total_assets is not None and shareholders_equity is not None:
                # Accounting identity: Assets = Equity + Liabilities
                total_liabilities = total_assets - shareholders_equity

            models.append(
                BalanceSheetModel(
                    symbol=symbol,
                    period=period,
                    fiscal_year=fiscal_year,
                    fiscal_quarter=None,
                    effective_date=date(fiscal_year, 3, 31),
                    total_assets=total_assets,
                    current_assets=other_assets,  # Screener's "Other Assets" ≈ current assets
                    cash_and_equivalents=self._get_row_value(df, "cash equivalents", col),
                    total_liabilities=total_liabilities,
                    current_liabilities=other_liabilities,  # Approximate
                    long_term_debt=borrowings,
                    shareholders_equity=shareholders_equity,
                )
            )

        return models

    def get_cash_flows(
        self, symbol: str, period: str = "annual", limit: int = 5
    ) -> List[CashFlowStatementModel]:
        symbol = self._normalize_for_screener(symbol)
        sections = self._parse_all_sections(symbol)
        df = sections.get("Cash Flows")

        if df is None or df.empty:
            logger.warning(f"No cash flow data from screener for {symbol}")
            return []

        if period == "quarter":
            logger.info("Screener does not provide quarterly cash flows")
            return []

        models: List[CashFlowStatementModel] = []
        year_cols = [c for c in df.columns[1:] if self._extract_fiscal_year(c)]
        year_cols = list(reversed(year_cols))  # newest first

        for col in year_cols[:limit]:
            fiscal_year = self._extract_fiscal_year(col)
            if not fiscal_year:
                continue

            # Try multiple possible row labels for capex
            capex = (
                self._get_row_value(df, "fixed assets purchased", col)
                or self._get_row_value(df, "fixed assets", col)
                or self._get_row_value(df, "purchase of fixed assets", col)
                or self._get_row_value(df, "capex", col)
            )

            models.append(
                CashFlowStatementModel(
                    symbol=symbol,
                    period=period,
                    fiscal_year=fiscal_year,
                    fiscal_quarter=None,
                    effective_date=date(fiscal_year, 3, 31),
                    operating_cash_flow=self._get_row_value(df, "operating activity", col),
                    capital_expenditure=capex,
                    investing_cash_flow=self._get_row_value(df, "investing activity", col),
                    financing_cash_flow=self._get_row_value(df, "financing activity", col),
                    net_cash_flow=self._get_row_value(df, "net cash flow", col),
                )
            )

        return models
    def get_latest_price(self, symbol: str, dt: date) -> Optional[float]:
        
        symbol = self._normalize_for_screener(symbol)
        soup = self._fetch_page(symbol)

        if soup is None:
            # Try pulling from already-parsed cache via get_company_overview
            try:
                overview = self.get_company_overview(symbol)
                return overview.get("price")
            except Exception:
                return None

        ratios_ul = soup.find("ul", id="top-ratios")
        if not ratios_ul:
            return None

        for li in ratios_ul.find_all("li"):
            name_span = li.find("span", class_="name")
            value_span = li.find("span", class_="number")

            if name_span and value_span:
                label = name_span.text.strip()
                if label == "Current Price":
                    val_text = value_span.text.replace(",", "").strip()
                    try:
                        return float(val_text)
                    except ValueError:
                        return None

        return None