from app.fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from app.fundamentals.models.financial_ratio_model import FinancialRatioModel
from app.fundamentals.models.fundamental_snapshot_model import FundamentalSnapshotModel
from app.registry.stock_registry import StockRegistry
from app.core.exceptions import ValidationError,NotFoundError
from app.fundamentals.validation.provider_sanity import assert_valid_fiscal_year

from typing import List
import logging

logger = logging.getLogger(__name__)
max_limit = 20

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
  
  def _select_by_year(self,models,fiscal_year):
    return next(
      (m for m in models if m.fiscal_year == fiscal_year),None
    )

  def _assert_sorted_desc(self,items):
    years = [x.fiscal_year for x in items]
    if years != sorted(years,reverse= True):
      raise ValidationError(
        code = "ORDERING_VIOLATION",
        message= "Fiscal Year Ordering Violation",
        details={"recieved":f"years {years} and sorted years {sorted(years,reverse=True)}"}
      )
    # print(years)
    return items
  def get_fundamental_snapshot(self,symbol:str,fiscal_year:int,period:str="annual") -> FundamentalSnapshotModel:

    logger.info(
        "Fetching fundamentals Snapshot",
        extra={"symbol": symbol, "period": period, "fiscal_year":fiscal_year}
    )

    fundamentals = self.get_fundamentals(symbol,fiscal_year)
    income_statement = self._select_by_year(fundamentals['income_statements'],fiscal_year)
    balance_sheet = self._select_by_year(fundamentals['balance_sheets'],fiscal_year)
    cash_flow = self._select_by_year(fundamentals['cash_flows'],fiscal_year)

    fy = income_statement.fiscal_year

    if balance_sheet.fiscal_year != fy or cash_flow.fiscal_year != fy:
      raise ValidationError(
        code= "FISCALYEAR_MISMATCH",
        message = f"Snapshot Fiscal Year Mismatch for symbol {symbol}",
        details={
          "received": f"Income Sheet Fiscal Year {fy}, Balance sheet Fiscal Year {balance_sheet.fiscal_year} and cash Flow Fiscal Year {cash_flow.fiscal_year}"
        }
      )

    if not income_statement or not balance_sheet or not cash_flow:raise NotFoundError(
                code="FUNDAMENTALS_NOT_FOUND",
                message=f"No fundamentals found for symbol {symbol}"
            )
    
    if income_statement.effective_date != balance_sheet.effective_date or income_statement.effective_date != cash_flow.effective_date:
      raise ValidationError(
        code ="NO_FILING_DATE",
        message=f"No Filing Date Was found for {symbol}"
      ) 

    return FundamentalSnapshotModel(
      symbol = self._normalize_symbol(symbol),
      period = period,
      fiscal_year = income_statement.fiscal_year,
      effective_date = income_statement.effective_date,
      income_statement = income_statement,
      balance_sheet= balance_sheet,
      cash_flow_statement= cash_flow,
      total_revenue = income_statement.total_revenue,
      net_income = income_statement.net_income,
      eps = income_statement.eps,
      operating_cash_flow = cash_flow.operating_cash_flow,
      total_liabilities = balance_sheet.total_liabilities,
      total_assets = balance_sheet.total_assets,
      shareholders_equity = balance_sheet.shareholders_equity
    )

  

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

    income_statements = filtered_income_statements
    balance_sheets = filtered_balance_sheets
    cash_flows = filtered_cash_flows

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
    fundamentals = self.get_fundamentals(symbol,period,limit)
    income_statements = fundamentals['income_statements']
    balance_sheets = fundamentals['balance_sheets']
    cash_flows = fundamentals['cash_flows']

    bs_map = { bs.fiscal_year : bs for bs in balance_sheets }
    cf_map = { cf.fiscal_year : cf for cf in cash_flows }
    ratio_fiscal_year = []

    for inc in income_statements:
    
      bs = bs_map.get(inc.fiscal_year,None)
      cf = cf_map.get(inc.fiscal_year,None)

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
        net_margin = round(net_margin,4) if net_margin else None,
        current_ratio = round(current_ratio,4) if current_ratio else None,
        debt_to_equity = round(debt_to_equity,4) if debt_to_equity else None,
        ocf_quality = round(ocf_quality,4) if ocf_quality else None,
        free_cash_flow = round(free_cash_flow,4) if free_cash_flow else None
        ))
        
    return ratio_fiscal_year