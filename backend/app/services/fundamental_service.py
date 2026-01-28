from fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from fundamentals.models.financial_ratio_model import FinancialRatioModel
from fundamentals.models.fundamental_snapshot_model import FundamentalSnapShotModel
from typing import List

class FundamentalService:
  def  __init__(self,provider:BaseFundamentalProvider):
    self.provider = provider

  def get_fundamental_snapshot(self,symbol:str,period:str="annual") -> FundamentalSnapShotModel:
    fundamenta_snap = self.provider.get_fundamental_snapshot(symbol,period)
    return fundamenta_snap

  def get_fundamentals(self,symbol:str,period:str="annual",limit:int=5) -> dict:
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
    
    return {
      "income_statements": sorted(income_statements,key = lambda x:x.fiscal_year,reverse=True),
      "balance_sheets": sorted(balance_sheets,key = lambda x:x.fiscal_year,reverse=True),
      "cash_flows": sorted(cash_flows,key = lambda x:x.fiscal_year,reverse=True)
    }
  

  def get_ratios(self,symbol:str,period:str="annual",limit:int=5) -> List[FinancialRatioModel]:
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
      ocf_quality  = cf.operating_cash_flow / inc.net_income if inc.net_income and inc.net_income !=0 else None

      free_cash_flow = None # From Cash Flow 
      free_cash_flow = cf.operating_cash_flow - abs(cf.capital_expenditures) if cf.operating_cash_flow and cf.capital_expenditures else None

      ratio_fiscal_year.append(
        FinancialRatioModel(
        symbol = symbol.upper().strip(),
        fiscal_year = inc.fiscal_year,
        net_margin = net_margin,
        current_ratio = current_ratio,
        debt_to_equity = debt_to_equity,
        ocf_quality = ocf_quality,
        free_cash_flow = free_cash_flow
        ))
        
      
    return ratio_fiscal_year