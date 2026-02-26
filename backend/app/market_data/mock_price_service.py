from app.market_data.base_price_service import BasePriceService
class MockPriceService(BasePriceService):
  def get_latest_price(self,symbol:str):
    #temporary value for testing, in real implementation this would call an external API or database
    return 100.0


# import requests


# class AlphaVantagePriceService(PriceService):

#     def __init__(self, api_key: str):
#         self.api_key = api_key

#     def get_latest_price(self, symbol: str) -> float:

#         url = f"https://www.alphavantage.co/query"
#         params = {
#             "function": "GLOBAL_QUOTE",
#             "symbol": symbol,
#             "apikey": self.api_key
#         }

#         response = requests.get(url, params=params)
#         data = response.json()

#         return float(data["Global Quote"]["05. price"])