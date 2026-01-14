class StockService:
  """
  Service class for stock-related operations.
  """
  def get_basic_info(self,symbol:str)->dict:
    return {
      "symbol":symbol,
      "message":"Service Layer working!"
    }