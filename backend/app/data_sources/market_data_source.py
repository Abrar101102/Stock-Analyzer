import yfinance as yf
import pandas as pd
from app.core.cache import redis_cache

class MarketDataSource:
  """
  Responsible for fetching raw market data
  """
  @redis_cache(expire_seconds=3600, returns_df=True)
  def fetch_history(self,symbol:str,period:str="1y"):
    try:
      ticker = yf.Ticker(symbol)
      print(f"Fetching data for:{symbol} with ticker {ticker}")
      df = ticker.history(period=period)
      return df
    except Exception as e:
      raise RuntimeError(f"Market Data Fetched Failed {str(e)}")