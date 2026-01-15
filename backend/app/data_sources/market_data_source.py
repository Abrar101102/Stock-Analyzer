import yfinance as yf
import pandas as pd

class MarketDataSource:
  """
  Responsible for fetching raw market data
  """
  def fetch_history(self,symbol:str,period:str="1y"):
    try:
      ticker = yf.Ticker(symbol)
      print(f"Fetching data for:{symbol} with ticker {ticker}")
      df = ticker.history(period=period)
      return df
    except Exception as e:
      raise RuntimeError(f"Market Data Fetched Failed {str(e)}")