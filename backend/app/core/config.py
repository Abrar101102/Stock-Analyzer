import urllib.parse

password = "Abrar@1011"
safe_password = urllib.parse.quote_plus(password)
DATABASE_URL = f"postgresql://stock_user:{safe_password}@localhost:5432/stock_analyzer"
ALPHA_VANTAGE_API_KEY = "JGPZOKCM2GN477A1"
