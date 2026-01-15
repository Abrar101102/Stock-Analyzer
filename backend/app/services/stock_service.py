from app.data_sources.market_data_source import MarketDataSource

class StockService:
  """
  Service class for stock-related operations.
  """
  def __init__(self):
    self.market_data = MarketDataSource()

  def get_basic_info(self,symbol:str)->dict:
    df = self.market_data.fetch_history(symbol)

    if df is None or df.empty:
      return {
        "Symbol":symbol,
        "Message":"No Market Data Found"
      }
    latest_price = df.iloc[-1]["Close"]
    return {
      "symbol":symbol,
      "latest_price": round(float(latest_price),2),
    }