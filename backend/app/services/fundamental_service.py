from fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from fundamentals.models.financial_ratio_model import FinancialRatioModel
from fundamentals.models.fundamental_snapshot_model import FundamentalSnapShotModel
from typing import List
import logging

logger = logging.getLogger(__name__)

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
    return symbol.upper().strip()

  def get_fundamental_snapshot(self,symbol:str,period:str="annual") -> FundamentalSnapShotModel:
    symbol = self._normalize_symbol(symbol)
    fundamentals = self.get_fundamentals(symbol)
    income_statement = fundamentals['income_statements'][0]
    balance_sheet = fundamentals['balance_sheets'][0]
    cash_flow = fundamentals['cash_flows'][0]

    return FundamentalSnapShotModel(
      symbol = symbol,
      period = period,
      fiscal_year = income_statement.fiscal_year,
      total_revenue = income_statement.total_revenue,
      net_income = income_statement.net_income,
      eps = income_statement.eps,
      operating_cash_flow = cash_flow.operating_cash_flow,
      total_liabilities = balance_sheet.total_liabilities,
      total_assets = balance_sheet.total_assets,
      shareholders_equity = balance_sheet.shareholders_equity
    )

  def get_fundamentals(self,symbol:str,period:str="annual",limit:int=5) -> dict:
    symbol = self._normalize_symbol(symbol)
    income_statements= self.provider.get_income_statements(symbol,period,limit)
    balance_sheets = self.provider.get_balance_sheets(symbol,period,limit)
    cash_flows = self.provider.get_cash_flows(symbol,period,limit)

    if not income_statements and not balance_sheets and not cash_flows:
      raise ValueError(f"No fundamental data found for symbol: {symbol}")
    elif not income_statements:
      raise ValueError(f"No income statement data found for symbol: {symbol}")
    elif not balance_sheets:
      raise ValueError(f"No balance sheet data found for symbol: {symbol}")
    elif not cash_flows:
      raise ValueError(f"No cash flow data found for symbol: {symbol}")
    
    # Filtered lists so mutation during iteration does not cause issues
    filtered_income_statements = []
    filtered_balance_sheets = []
    filtered_cash_flows = []

    for inc in income_statements:
      if inc.fiscal_year is None:
        logger.warning(f"Income statement data missing fiscal year for symbol: {symbol}")
        continue
      if inc.total_revenue is None and inc.net_income is None:
        continue
      filtered_income_statements.append(inc)

    for bs in balance_sheets:
      if bs.fiscal_year is None:
        logger.warning(f"Balance sheet data missing fiscal year for symbol: {symbol}")
        continue
      if bs.total_assets is None and bs.total_liabilities is None and bs.shareholders_equity is None:
        continue
      filtered_balance_sheets.append(bs)
    
    for cf in cash_flows:
      if cf.fiscal_year is None:
        logger.warning(f"Cash flow data missing fiscal year for symbol: {symbol}")
        continue
      if cf.operating_cash_flow is None:
        continue
      filtered_cash_flows.append(cf)

    income_statements = filtered_income_statements
    balance_sheets = filtered_balance_sheets
    cash_flows = filtered_cash_flows

    return {
      "income_statements": sorted(income_statements,key = lambda x:x.fiscal_year,reverse=True)[:limit],
      "balance_sheets": sorted(balance_sheets,key = lambda x:x.fiscal_year,reverse=True)[:limit],
      "cash_flows": sorted(cash_flows,key = lambda x:x.fiscal_year,reverse=True)[:limit]
    }
  

  def get_ratios(self,symbol:str,period:str="annual",limit:int=5) -> List[FinancialRatioModel]:
    symbol = self._normalize_symbol(symbol)
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
      free_cash_flow = cf.operating_cash_flow - abs(cf.capital_expenditures) if cf.operating_cash_flow and cf.capital_expenditures else None

      ratio_fiscal_year.append(
        FinancialRatioModel(
        symbol = symbol,
        fiscal_year = inc.fiscal_year,
        net_margin = round(net_margin,4) if net_margin else None,
        current_ratio = round(current_ratio,4) if current_ratio else None,
        debt_to_equity = round(debt_to_equity,4) if debt_to_equity else None,
        ocf_quality = round(ocf_quality,4) if ocf_quality else None,
        free_cash_flow = round(free_cash_flow,4) if free_cash_flow else None
        ))
        
      
    return ratio_fiscal_year