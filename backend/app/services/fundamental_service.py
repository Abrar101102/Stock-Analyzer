from fundamentals.data_providers.base_fundamental_provider import BaseFundamentalProvider

class FundamentalService:
  def  __init__(self,provider:BaseFundamentalProvider):
    self.provider = provider

  def get_fundamental_snapshot(self,symbol:str,period:str="annual",limit:int=5):
    pass
  def get_fundamentals(self,symbol:str,period:str="annual",limit:int=5):
    pass
  def get_ratios(self,symbol:str,period:str="annual",limit:int=5):
    pass