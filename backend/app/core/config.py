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

print(f"Using NEWS_API_KEY: {NEWS_API_KEY}")