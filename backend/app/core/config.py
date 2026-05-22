import urllib.parse
import os
from dotenv import load_dotenv,find_dotenv

load_dotenv()
dotenv_path = find_dotenv()
print(f"Found .env at: {dotenv_path}")

password = "Abrar@1011"
safe_password = urllib.parse.quote_plus(password)
DATABASE_URL = f"postgresql://stock_user:{safe_password}@localhost:5432/stock_analyzer"
ALPHA_VANTAGE_API_KEY = "JGPZOKCM2GN477A1"
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


class Settings:
	def __init__(self) -> None:
		self.LLM_provider = os.getenv("LLM_PROVIDER", "local").lower()
		self.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
		self.LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH", "models/mistral-7b-instruct-v0.3.Q4_K_M.gguf")
		self.LLM_LORA_PATH = os.getenv("LLM_LORA_PATH", "models/model-f16.gguf")
		self.LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "120"))
		self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
		self.COMPOSITE_WEIGHT_FUNDAMENTAL = float(os.getenv("COMPOSITE_WEIGHT_FUNDAMENTAL", "0.25"))
		self.COMPOSITE_WEIGHT_TECHNICAL = float(os.getenv("COMPOSITE_WEIGHT_TECHNICAL", "0.25"))
		self.COMPOSITE_WEIGHT_SENTIMENT = float(os.getenv("COMPOSITE_WEIGHT_SENTIMENT", "0.25"))
		self.COMPOSITE_WEIGHT_VALUATION = float(os.getenv("COMPOSITE_WEIGHT_VALUATION", "0.25"))
		self.FRED_API_KEY = os.getenv("FRED_API_KEY", "")
		self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


settings = Settings()

print(f"Using NEWS_API_KEY: {NEWS_API_KEY}")