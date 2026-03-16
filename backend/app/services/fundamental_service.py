from app.fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from app.fundamentals.models.financial_ratio_model import FinancialRatioModel
from app.fundamentals.models.fundamental_snapshot_model import FundamentalSnapshotModel
from app.registry.stock_registry import StockRegistry
from app.registry.symbol_resolver import SymbolResolver
from app.core.exceptions import ValidationError,NotFoundError
from app.fundamentals.validation.provider_sanity import assert_valid_fiscal_year
from dataclasses import asdict
from typing import List
import logging

logger = logging.getLogger(__name__)
max_limit = 50

class FundamentalService:
  """
Service layer responsibilities (Unit 6.3.4):
- Input sanitization (symbol normalization)
- Validation & filtering of incomplete provider data
- Limiting & ordering
- Cross-statement alignment (by fiscal_year)
- Derived metrics (ratios)


Providers MUST stay dumb: no limits, no assumptions, no index [0].
"""
  def  __init__(self,provider:BaseFundamentalProvider):
    self.provider = provider
    
  def _normalize_symbol(self,symbol:str)->str:
    # Check if symbol is in registry and return normalized version if it exists 
    stock = StockRegistry.get_stock(symbol)
    return stock.yahoo_symbol
  
  def _validate_limit(self,limit:int)->int:
    if limit <=0:
      raise ValidationError(
        code = "INVALID_LIMIT",
        message = "Limit Must be Greater than Zero",
        details = {"received":limit} 
      )
    if limit > max_limit:
      raise ValidationError(
        code = "INVALID_LIMIT",
        message = f"Limit exceeds maximum allowed value of {max_limit}",
        details = {"received":limit} 
      )
      
    if limit is None:
      raise ValidationError(
        code = "INVALID_LIMIT",
        message = "Limit Must be Provided",
        details = {"received":None} 
      )
    if not isinstance(limit,int):
      raise ValidationError(
        code = "INVALID_LIMIT",
        message = "Limit Must be of Type Integer",
        details = {"received":limit} 
      )
    return limit
  
  def _select_snapshot(self, statements, fiscal_year, period: str, fiscal_quarter=None):
    print(f"Selecting snapshot for fiscal_year={fiscal_year}, period={period}, fiscal_quarter={fiscal_quarter}")
    print(f"Statement value is ",statements)
    for s in statements:
        # 1. Use direct attribute access (s.fiscal_year)
        # 2. Wrap both sides in int() to ignore type mismatches
        try:
            if period == "annual":
                if int(s.fiscal_year) == int(fiscal_year):
                    return s
            
            elif period == "quarter":
                print(f"DEBUG: Search Target FY type: {type(fiscal_year)}, QTR type: {type(fiscal_quarter)}")
                if (int(s.fiscal_year) == int(fiscal_year) and 
                    int(s.fiscal_quarter) == int(fiscal_quarter)):
                    print(f"DEBUG: Search Target FY type: {fiscal_year}, QTR type: {fiscal_quarter}")
                    return s
        except (ValueError, TypeError, AttributeError):
            # This handles cases where fiscal_quarter might be None
            continue
    print(f"FAILED TO FIND MATCH in {len(statements)} records")
    return None

  def _assert_sorted_desc(self,items):
    keys = [
        (x.fiscal_year, getattr(x, "fiscal_quarter", None))
        for x in items
    ]

    sorted_keys = sorted(
        keys,
        reverse=True
    )

    if keys != sorted_keys:
        raise ValidationError(
            code="ORDERING_VIOLATION",
            message="Fiscal ordering violation",
            details={"received": keys, "expected": sorted_keys}
        )

    return items
  
  def _period_key(self,model):
    return(
      model.fiscal_year,getattr(model,"fiscal_quarter",None)
    )
  def _sort_desc(self, items):
    return sorted(
        items,
        key=lambda x: (x.fiscal_year, getattr(x, "fiscal_quarter", 0)),
        reverse=True
    )
  
  # In fundamental_service.py — not in the provider
  def get_available_periods(self, symbol: str, period: str):
      """Returns only periods where all 3 filtered statements exist."""
      # symbol = self._normalize_symbol(symbol)
      
      # Use provider methods directly (no limit, no fiscal_year filter)
      income_statements = self.provider.get_income_statements(symbol, period)
      balance_sheets    = self.provider.get_balance_sheets(symbol, period)
      cash_flows        = self.provider.get_cash_flows(symbol, period)

      # Apply same filtering logic as get_fundamentals
      def filter_income(stmts):
          return {
              self._period_key(s) for s in stmts
              if s.fiscal_year is not None
              and not (s.total_revenue is None and s.net_income is None)
          }
      def filter_balance(stmts):
          return {
              self._period_key(s) for s in stmts
              if s.fiscal_year is not None
              and not (s.total_assets is None and s.total_liabilities is None and s.shareholders_equity is None)
          }
      def filter_cashflow(stmts):
          return {
              self._period_key(s) for s in stmts
              if s.fiscal_year is not None
              and s.operating_cash_flow is not None
          }

      inc_periods = filter_income(income_statements)
      bs_periods  = filter_balance(balance_sheets)
      cf_periods  = filter_cashflow(cash_flows)

      if period == "quarter":
        return inc_periods

      return inc_periods & bs_periods & cf_periods
  
  def get_quarterly_income_snapshot(self, symbol: str, fiscal_year: int, fiscal_quarter: int):
    # IMPORTANT: do not call get_fundamentals() here because it enforces BS+CF existence.
    limit = 50  # pull enough quarters to cover multiple years
    
    # normalize for the provider (Yahoo symbol)
    provider_symbol = self._normalize_symbol(symbol)

    income_statements = self.provider.get_income_statements(provider_symbol, "quarter", limit)

    if not income_statements:
        raise NotFoundError(
            code="FUNDAMENTALS_NOT_FOUND",
            message=f"No quarterly income statements found for symbol {symbol}"
        )

    # Filter income statements like you do elsewhere
    filtered_income = []
    for inc in income_statements:
        assert_valid_fiscal_year(inc.fiscal_year, provider_symbol)
        if inc.fiscal_year is None:
            continue
        if inc.total_revenue is None and inc.net_income is None:
            continue
        filtered_income.append(inc)

    # Sort DESC so _select_snapshot works predictably
    filtered_income = self._sort_desc(filtered_income)

    income = self._select_snapshot(
        filtered_income,
        fiscal_year,
        "quarter",
        fiscal_quarter
    )

    if not income:
        raise NotFoundError(
            code="FUNDAMENTALS_NOT_FOUND",
            message=f"No quarterly income statement found for {symbol} FY{fiscal_year} Q{fiscal_quarter}"
        )

    return {
        "symbol": symbol,
        "period": "quarter",
        "fiscal_year": income.fiscal_year,
        "fiscal_quarter": income.fiscal_quarter,
        "effective_date": income.effective_date,
        "income_statement": income,
        "balance_sheet": None,
        "cash_flow_statement": None,
    }
  
  def get_fundamental_snapshot(self, symbol: str, fiscal_year: int, period: str = "annual", fiscal_quarter: int | None = None) -> FundamentalSnapshotModel:

    logger.info(
        "Fetching fundamentals Snapshot",
        extra={"symbol": symbol, "period": period, "fiscal_year": fiscal_year}
    )

    fundamentals = self.get_fundamentals(symbol, fiscal_year, period=period)
    income_statement = self._select_snapshot(fundamentals['income_statements'], fiscal_year, period, fiscal_quarter)
    balance_sheet = self._select_snapshot(fundamentals['balance_sheets'], fiscal_year, period, fiscal_quarter)
    cash_flow = self._select_snapshot(fundamentals['cash_flows'], fiscal_year, period, fiscal_quarter)

    if not income_statement or not balance_sheet or not cash_flow:
      raise NotFoundError(
        code="FUNDAMENTALS_NOT_FOUND",
        message=f"No fundamentals found for symbol {symbol}"
      )

    fy = income_statement.fiscal_year

    if balance_sheet.fiscal_year != fy or cash_flow.fiscal_year != fy:
      raise ValidationError(
        code="FISCALYEAR_MISMATCH",
        message=f"Snapshot Fiscal Year Mismatch for symbol {symbol}",
        details={
          "received": f"Income Sheet FY {fy}, Balance sheet FY {balance_sheet.fiscal_year}, Cash Flow FY {cash_flow.fiscal_year}"
        }
      )

    # ─── FIXED: Reconcile effective_date across mixed providers ───
    # When data comes from different providers (Yahoo vs Screener),
    # effective_dates may differ (actual filing date vs fiscal year end).
    # Fiscal year match is the real guarantee of alignment.
    # Pick the most informative date and normalize across all three.
    effective_date = self._reconcile_effective_date(
        income_statement, balance_sheet, cash_flow
    )

    return FundamentalSnapshotModel(
      symbol=symbol,
      period=period,
      fiscal_year=income_statement.fiscal_year,
      fiscal_quarter=income_statement.fiscal_quarter,
      effective_date=effective_date,
      income_statement=income_statement,
      balance_sheet=balance_sheet,
      cash_flow_statement=cash_flow,
      total_revenue=income_statement.total_revenue,
      net_income=income_statement.net_income,
      eps=income_statement.eps,
      operating_cash_flow=cash_flow.operating_cash_flow,
      total_liabilities=balance_sheet.total_liabilities,
      total_assets=balance_sheet.total_assets,
      shareholders_equity=balance_sheet.shareholders_equity
    )

  def _reconcile_effective_date(self, income, balance_sheet, cash_flow):
    """
    Reconcile effective_date when statements come from different providers.
    
    Priority logic:
    1. If all three dates match → use that date (ideal case)
    2. If dates differ → prefer the non-March-31 date (it's a real filing date 
       from Yahoo's earnings_map, more informative than screener's hardcoded date)
    3. If all are March 31 → that's fine, use it (all from screener)
    """
    dates = [
        income.effective_date,
        balance_sheet.effective_date,
        cash_flow.effective_date
    ]

    # Case 1: All match — ideal
    if dates[0] == dates[1] == dates[2]:
      return dates[0]

    logger.info(
      "Reconciling mismatched effective_dates from mixed providers",
      extra={
        "income_date": str(dates[0]),
        "balance_date": str(dates[1]),
        "cashflow_date": str(dates[2]),
      }
    )

    # Case 2: Pick the real filing date (non-March-31, non-default)
    # A date that's NOT exactly March 31 or Dec 31 is likely a real 
    # earnings filing date from Yahoo
    from datetime import date as date_type
    for d in dates:
      if d and not (d.month == 3 and d.day == 31):
        return d

    # Case 3: All are fiscal year end dates — just use the first one
    return dates[0]
  

  

  def get_fundamentals(self,symbol:str,fiscal_year:int,period:str="annual",limit:int=5) -> dict:

    logger.info(
        "Fetching fundamentals",
        extra={"symbol": symbol, "period": period, "limit": limit}
    )
    
    limit = self._validate_limit(limit)
    symbol = self._normalize_symbol(symbol)

    income_statements= self.provider.get_income_statements(symbol,period)
    balance_sheets = self.provider.get_balance_sheets(symbol,period)
    cash_flows = self.provider.get_cash_flows(symbol,period)

    logger.debug(
        "Raw provider counts",
        extra={
            "income": len(income_statements),
            "balance": len(balance_sheets),
            "cashflow": len(cash_flows)
        }
    )
    print("Raw Income Statements",income_statements)
    print("Raw Balance Sheets",balance_sheets)
    print("Raw Cash Flows",cash_flows)
    if not income_statements and not balance_sheets and not cash_flows:
      raise NotFoundError(
                code="FUNDAMENTALS_NOT_FOUND",
                message=f"No fundamentals found for symbol {symbol}"
            )
    elif not income_statements:
      raise NotFoundError(
                code="FUNDAMENTALS_NOT_FOUND",
                message=f"No Income Statement found for symbol {symbol}"
            )
    elif not balance_sheets:
      raise NotFoundError(
                code="FUNDAMENTALS_NOT_FOUND",
                message=f"No Balance Sheet found for symbol {symbol}"
            )
    elif not cash_flows:
      raise NotFoundError(
                code="FUNDAMENTALS_NOT_FOUND",
                message=f"No Cash Flows found for symbol {symbol}"
            )
    
    # Filtered lists so mutation during iteration does not cause issues
    filtered_income_statements = []
    filtered_balance_sheets = []
    filtered_cash_flows = []

    for inc in income_statements:
      assert_valid_fiscal_year(inc.fiscal_year,symbol)
      if inc.fiscal_year is None:
        logger.warning(f"Income statement data missing fiscal year for symbol: {symbol}")
        continue
      if inc.total_revenue is None and inc.net_income is None:
        continue
      filtered_income_statements.append(inc)

    for bs in balance_sheets:
      assert_valid_fiscal_year(bs.fiscal_year,symbol)
      if bs.fiscal_year is None:
        logger.warning(f"Balance sheet data missing fiscal year for symbol: {symbol}")
        continue
      if bs.total_assets is None and bs.total_liabilities is None and bs.shareholders_equity is None:
        continue
      filtered_balance_sheets.append(bs)
    
    for cf in cash_flows:
      assert_valid_fiscal_year(cf.fiscal_year,symbol)
      if cf.fiscal_year is None:
        logger.warning(f"Cash flow data missing fiscal year for symbol: {symbol}")
        continue
      if cf.operating_cash_flow is None:
        continue
      filtered_cash_flows.append(cf)

    logger.info(
      "Filtered fundamentals",
      extra={
        "symbol": symbol,
        "income_years": filtered_income_statements,
        "balance_years": filtered_balance_sheets,
        "cashflow_years": filtered_cash_flows,
      }
    )

    income_statements = self._sort_desc(filtered_income_statements)
    balance_sheets = self._sort_desc(filtered_balance_sheets)
    cash_flows = self._sort_desc(filtered_cash_flows)
    print("Filtered Income Statements",income_statements)
    print("Filtered Balance Sheets",balance_sheets)
    print("Filtered Cash Flows",cash_flows)
    
    income_sorted = self._assert_sorted_desc(income_statements)
    balance_sorted = self._assert_sorted_desc(balance_sheets)
    cashflows_sorted = self._assert_sorted_desc(cash_flows)
    
    return {
      "income_statements":income_sorted[:limit],
      "balance_sheets": balance_sorted[:limit],
      "cash_flows": cashflows_sorted[:limit]
    }
  

  def get_ratios(self,symbol:str,period:str="annual",limit:int=5) -> List[FinancialRatioModel]:
  
    logger.info(
        "Fetching Ratios",
        extra={"symbol": symbol, "period": period,"limit":limit}
    )
    limit = self._validate_limit(limit)
    fundamentals = self.get_fundamentals(symbol,fiscal_year=None,period=period,limit=limit)
    income_statements = fundamentals['income_statements']
    balance_sheets = fundamentals['balance_sheets']
    cash_flows = fundamentals['cash_flows']

    bs_map = { self._period_key(bs): bs for bs in balance_sheets }
    cf_map = { self._period_key(cf): cf for cf in cash_flows }
    ratio_fiscal_year = []

    for inc in income_statements:
      key = self._period_key(inc)
    
      bs = bs_map.get(key,None)
      cf = cf_map.get(key,None)

      if not bs or not cf:
        continue

      net_margin = None #From Income Statement

      net_margin = inc.net_income /inc.total_revenue if inc.total_revenue and inc.total_revenue !=0 else None

      current_ratio = None # From Balance Sheet

      current_ratio = bs.current_assets / bs.current_liabilities if bs.current_liabilities and bs.current_liabilities !=0 else None

      debt_to_equity = None # From Balance Sheet

      debt_to_equity = bs.total_liabilities / bs.shareholders_equity if bs.shareholders_equity and bs.shareholders_equity != 0 else None

      ocf_quality = None # From Cash Flow 
      ocf_quality  = cf.operating_cash_flow / abs(inc.net_income) if inc.net_income and inc.net_income !=0 else None

      free_cash_flow = None # From Cash Flow 
      free_cash_flow = cf.operating_cash_flow - abs(cf.capital_expenditure) if cf.operating_cash_flow and cf.capital_expenditure else None

      ratio_fiscal_year.append(
        FinancialRatioModel(
        symbol = self._normalize_symbol(symbol),
        fiscal_year = inc.fiscal_year,
        fiscal_quarter = inc.fiscal_quarter,
        net_margin = round(net_margin,4) if net_margin else None,
        current_ratio = round(current_ratio,4) if current_ratio else None,
        debt_to_equity = round(debt_to_equity,4) if debt_to_equity else None,
        ocf_quality = round(ocf_quality,4) if ocf_quality else None,
        free_cash_flow = round(free_cash_flow,4) if free_cash_flow else None
        ))
        
    return ratio_fiscal_year
  
  def missing_years_snapshots(self,symbol:str,period:str="annual",stored_periods=None)-> List[FundamentalSnapshotModel]:
    """
    Backfills missing years by fetching additional data from provider and creating synthetic snapshots for missing years.
    This is a best effort attempt to fill in gaps in data but is not guaranteed to fill all gaps due to provider limitations.
    """
    stored_periods= stored_periods or set()
    symbol_for_available_period = self._normalize_symbol(symbol)
    available_periods = self.get_available_periods(symbol_for_available_period,period)
    print("Period Given",period)
    print("Available Periods",available_periods)
    if not available_periods:
      raise NotFoundError(
                code="FUNDAMENTALS_NOT_FOUND",
                message=f"No fundamentals found for symbol {symbol}"
            )
    array_of_snapshots = []
    missing_periods = set(available_periods) - stored_periods
    for item in missing_periods:
      if period == "annual":
        fiscal_year = item
        snapshot = self.get_fundamental_snapshot(
          symbol=symbol,
          fiscal_year=fiscal_year,
          period="annual"
        )
      elif period == "quarter":
        fiscal_year,fiscal_quarter = item
        snapshot = self.get_quarterly_income_snapshot(
          symbol=symbol,
          fiscal_year=fiscal_year,
          fiscal_quarter=fiscal_quarter
          
        )
      array_of_snapshots.append(snapshot)


    return array_of_snapshots
