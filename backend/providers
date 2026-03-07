1. Alpha Vantage (⭐ Recommended First Addition)
   Free tier: 25 API calls/day (standard), 75/min with free key
   What it provides: OHLCV price history, income statement, balance sheet, cash flow, earnings, company overview (PE, EPS, market cap, sector, etc.)
   Why it fits your project: It directly provides fundamental data (financial statements) which aligns perfectly with your fundamental_snapshots table design
   Reliability: Very stable API, rarely goes down, well-documented
   Python library: alpha_vantage or just raw requests
   Here's how a provider would look in your architecture:

2. Financial Modeling Prep (FMP)
   Free tier: 250 API calls/day
   What it provides: Full financial statements, ratios, DCF valuation, stock screener, sector performance, earnings calendar
   Why it fits: Provides pre-computed ratios and DCF — great for your valuation_service.py and derived_metrics_service.py
3. Twelve Data
   Free tier: 800 API calls/day, 8 per minute
   What it provides: Real-time & historical prices, technical indicators (RSI, MACD, Bollinger Bands built-in), forex, crypto
   Why it fits: Since you already have ta (technical analysis) in your requirements, Twelve Data can give you pre-computed indicators as a cross-reference
4. Polygon.io
   Free tier: 5 API calls/min, delayed data
   What it provides: Stocks, options, forex, crypto, news, reference data (ticker details, market holidays)
   Why it fits: News data is key for your "external world elements" vision
