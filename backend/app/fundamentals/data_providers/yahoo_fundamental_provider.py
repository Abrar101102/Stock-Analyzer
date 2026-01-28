from fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from models.balance_sheet_model import BalanceSheetModel
from models.income_statement_model import IncomeStatementModel
from models.cash_flow_model import CashFlowModel
from models.fundamental_snapshot_model import FundamentalSnapshotModel

import yfinance as yf
from typing import List,Optional,Dict

class YahooFundamentalProvider(BaseFundamentalProvider):
  def get_balance_sheets(self, symbol, period = 'annual', limit = 5)->List[IncomeStatementModel]:
   """Returns last N years of balance sheet statements for the given symbol from Yahoo Finance"""
   ticker = yf.Ticker(symbol)
   raw_bs = ticker.balance_sheet
   models:List[BalanceSheetModel] = []
   for fiscal_year in raw_bs.columns[:limit]:
     models.append(
       BalanceSheetModel(
         symbol = symbol,
         period = period,
         fiscal_year = int(fiscal_year),
         total_assets = raw_bs.get('Total Assets',{}).get(fiscal_year),
         current_assets = raw_bs.get('Current Assets',{}).get(fiscal_year),
         cash_and_equivalents = raw_bs.get('Cash And Cash Equivalents',{}).get(fiscal_year),
         total_liabilities = raw_bs.get('Total Liabilities and Net Minorities Interest',{}).get(fiscal_year),
         current_liabilities = raw_bs.get('Current Liabilities',{}).get(fiscal_year),
         long_term_debt = raw_bs.get('Long Term Debt',{}).get(fiscal_year),
         shareholders_equity = raw_bs.get("Shareholders' Equity",{}).get(fiscal_year)
       )
       
     )
   return models

  def get_income_statements(self, symbol, period = 'annual', limit = 5)->List[IncomeStatementModel]:
    """Returns last N years of income statements for the given symbol from Yahoo Finance"""
    ticker = yf.Ticker(symbol)
    raw_is = ticker.financials # Raw income Statement Data from yfinance
    models:List[IncomeStatementModel] = []
    for fiscal_year in raw_is.columns[:limit]:
      models.append(
        IncomeStatementModel(
          symbol = symbol,
          period = period,
          fiscal_year = fiscal_year,
          total_revenue = raw_is.get("Total Revenue",{}).get(fiscal_year),
          operating_income = raw_is.get("Operating Income",{}).get(fiscal_year),
          net_income = raw_is.get('Net Income',{}).get(fiscal_year),
          eps =  None
        )
      )
    return models

  def get_cash_flows(self, symbol, period = 'annual', limit = 5)->List[CashFlowModel]:
    """Returns last N years of cash flow statements for the given symbol from Yahoo Finance"""
    ticker = yf.Ticker(symbol)
    raw_cf = ticker.cashflow

    models:List[CashFlowModel] = []

    for fiscal_year in raw_cf.columns[:limit]:
      models.append(
        CashFlowModel(
          symbol = symbol,
          period = period,
          fiscal_year = fiscal_year,
          operating_cash_flow = raw_cf.get("Toal Cash Flow From Operating Activities",{}).get(fiscal_year),
          capital_expenditure = raw_cf.get("Capital Expenditures",{}).get(fiscal_year),
          investing_cash_flow = raw_cf.get("Total Cash Flows From Investing Activities",{}).get(fiscal_year),
          financing_cash_flow = raw_cf.get("Total Cash From Financing Activities",{}).get(fiscal_year),
          net_cash_flow = raw_cf.get("Total Cash From Operating Activities",{}).get(fiscal_year)
        )
      )

    return models

  def get_fundamental_snapshot(self, symbol, period = 'annual', fiscal_year = None) -> FundamentalSnapshotModel:
    """Returns a compact snapshot of fundamentals(headline metrics derived from statements) for the given symbol from Yahoo Finance"""
    income_statement = self.get_income_statement(symbol, period, limit=5)[0]
    balance_sheet = self.get_balance_sheet(symbol, period, limit=5)[0]
    cash_flow_statement = self.get_cash_flows(symbol, period, limit=5)[0]

    return FundamentalSnapshotModel(
      symbol = symbol,
      period = period,
      fiscal_year = income_statement.fiscal_year,
      total_revenue = income_statement.total_revenue,
      net_income = income_statement.net_income,
      eps = income_statement.eps,
      operating_cash_flow = cash_flow_statement.operating_cash_flow,
      total_liabilities = balance_sheet.total_liabilities,
      total_assets = balance_sheet.total_assets,
      shareholders_equity = balance_sheet.shareholders_equity
    )