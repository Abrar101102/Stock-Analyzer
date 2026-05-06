"""Quick smoke test — run standalone to verify scraping works."""
from app.fundamentals.data_providers.screener_provider import ScreenerFundamentalProvider

provider = ScreenerFundamentalProvider()

# Test with a well-known Indian stock
print("=== INCOME STATEMENTS ===")
income = provider.get_income_statements("RELIANCE", "annual", 5)
for i in income:
    print(f"  FY{i.fiscal_year}: Revenue={i.total_revenue}, Net Income={i.net_income}, EPS={i.eps}")

print("\n=== BALANCE SHEETS ===")
bs = provider.get_balance_sheets("RELIANCE", "annual", 5)
for b in bs:
    print(f"  FY{b.fiscal_year}: Assets={b.total_assets}, Equity={b.shareholders_equity}")

print("\n=== CASH FLOWS ===")
cf = provider.get_cash_flows("RELIANCE", "annual", 5)
for c in cf:
    print(f"  FY{c.fiscal_year}: OpCF={c.operating_cash_flow}, Capex={c.capital_expenditure}")

print("\n=== QUARTERLY INCOME ===")
q_income = provider.get_income_statements("TCS", "quarter", 4)
for q in q_income:
    print(f"  FY{q.fiscal_year} Q{q.fiscal_quarter}: Revenue={q.total_revenue}, NI={q.net_income}")