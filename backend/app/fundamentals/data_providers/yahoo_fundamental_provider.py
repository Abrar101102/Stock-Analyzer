from fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider
from models.balance_sheet_model import BalanceSheetModel
from models.income_statement_model import IncomeStatementModel
from models.cash_flow_model import CashFlowModel
from models.fundamental_snapshot_model import FundamentalSnapshotModel

import yfinance as yf
from typing import List,Optional,Dict

class YahooFundamentalProvider(BaseFundamentalProvider):
  def get_balance_sheet(self, symbol, period = 'annual', limit = 5)->List[IncomeStatementModel]:
   pass
  def get_balance_sheets(self, symbol, period = 'annual', limit = 5)->List[BalanceSheetModel]:
    pass
  def get_cash_flows(self, symbol, period = 'annual', limit = 5)->List[CashFlowModel]:
    pass
  def get_fundamental_snapshot(self, symbol, period = 'annual', fiscal_year = None) -> FundamentalSnapshotModel:
    pass