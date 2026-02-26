from abc import ABC,abstractmethod

class BasePriceService(ABC):
  @abstractmethod
  def get_latest_price(self,symbol:str,date):
    pass