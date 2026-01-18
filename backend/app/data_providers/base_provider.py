from abc import ABC, abstractmethod
from typing import List,Dict

class MarketDataProvider(ABC):
  """
  Abstract contract for any data provider
  """

  @abstractmethod
  def get_price_history(self,symbol:str,period:str) -> List[Dict]:
    """
    Fetch historical OHLC price data.
    
    :param symbol: provider specific symbol
    :param period: 1mo,3mo,6mo,1y,2y,5y
    """
    pass

  