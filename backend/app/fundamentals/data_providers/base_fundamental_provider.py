from abc import ABC,abstractmethod
from typing import List,Dict,Optional

from app.fundamentals.models.balance_sheet_model import BalanceSheetModel
from app.fundamentals.models.income_statement_model import IncomeStatementModel
from app.fundamentals.models.cash_flow_model import CashFlowStatementModel
from app.fundamentals.models.fundamental_snapshot_model import FundamentalSnapshotModel

class BaseFundamentalProvider(ABC):
  """
  Base interface for fundamental data providers. ANy Provider (yahoo, alpha vantage etc) must implement this interface.
  """
  @abstractmethod
  def get_income_statements(self,symbol:str,period:str = 'annual',limit : int = 5) -> List[IncomeStatementModel]:
    """ Fetch Income Statements"""
    pass
  @abstractmethod
  def get_balance_sheets(self,symbol:str,period:str='annual',limit:int=5)->List[BalanceSheetModel]:
    """Fetch Balance Sheets"""
    pass
  @abstractmethod
  def get_cash_flows(self,symbol:str,period:str='annual',limit:int=5)->List[CashFlowStatementModel]:
    """Fetch Cash Flow Statements"""
    pass