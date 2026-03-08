import requests
from typing import List, Dict
from app.data_providers.base_provider import MarketDataProvider
from app.core.config import ALPHA_VANTAGE_API_KEY

class AlphaVantageProvider(MarketDataProvider):
    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self.api_key = ALPHA_VANTAGE_API_KEY

    def get_price_history(self, symbol: str, period: str) -> List[Dict]:
        # Map your period format to Alpha Vantage's outputsize
        outputsize = "compact" if period in ["1mo", "3mo"] else "full"
        
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": self.api_key,
        }
        response = requests.get(self.BASE_URL, params=params)
        raw = response.json().get("Time Series (Daily)", {})

        data = []
        for date_str, values in raw.items():
            data.append({
                "date": date_str,
                "open": float(values["1. open"]),
                "high": float(values["2. high"]),
                "low": float(values["3. low"]),
                "close": float(values["4. close"]),
                "volume": int(values["5. volume"]),
            })
        return sorted(data, key=lambda x: x["date"])
