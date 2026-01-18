import yfinance as yf 
from typing import List,Dict
from app.data_providers.base_provider import MarketDataProvider

class YahooMarketDataProvider(MarketDataProvider):

  def get_price_history(self,symbol:str,period:str) -> List[Dict]:
    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period)

    data = []

    for index,row in history.iterrows():
      data.append({
        "date": index.strftime("%Y-%m-%d"),
        "open": float(row["Open"]),
        "high": float(row["High"]),
        "low": float(row["Low"]),
        "close": float(row["Close"]),
        "volume": float(row["Volume"])
      })

    return data