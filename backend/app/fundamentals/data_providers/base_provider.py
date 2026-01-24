from abc import ABC,abstractmethod
from typing import List,Dict,Optional

from models.balance_sheet_model import BalanceSheetModel
from models.income_statement_model import IncomeStatementModel
from models.cash_flow_model import CashFlowModel
from models.fundamental_snapshot_model import FundamentalSnapshotModel

class BaseFundamentalProvider(ABC):
  """
  Base interface for fundamental data providers. ANy Provider (yahoo, alpha vantage etc) must implement this interface.
  """
  @abstractmethod
  def get_balance_sheet(self,symbol:str,period:str = 'annual',limit : int = 5) -> List[IncomeStatementModel]:
    """ Fetch Income Statements"""
    pass
  @abstractmethod
  def get_balance_sheets(self,symbol:str,period:str='annual',limit:int=5)->List[BalanceSheetModel]:
    """Fetch Balance Sheets"""
    pass
  @abstractmethod
  def get_cash_flows(self,symbol:str,period:str='annual',limit:int=5)->List[CashFlowModel]:
    """Fetch Cash Flow Statements"""
    pass
  @abstractmethod
  def get_fundamental_snapshot(self,symbol:str,period:str='annual',fiscal_year:Optional[int]=None)->FundamentalSnapshotModel:
    """Returns a compact snapshot of fundamentals(headline metrics derived from statements)"""
    pass