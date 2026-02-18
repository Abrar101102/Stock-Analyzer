from app.fundamentals.models.fundamental_snapshot_model import FundamentalSnapshotModel


class FundamentalSnapshotMapper:

    @staticmethod
    def to_domain(entity):
        data = entity.data or {}

        income = data.get("income_statement", {})
        cashflow = data.get("cash_flow", {})
        balance = data.get("balance_sheet", {})

        return FundamentalSnapshotModel(
            symbol=entity.symbol,
            period=data.get("period"),
            fiscal_year=entity.fiscal_year,
            effective_date=entity.effective_date,
            income_statement=income,
            cash_flow_statement=cashflow,
            balance_sheet=balance,
            total_revenue=income.get("totalRevenue"),
            net_income=income.get("netIncome"),
            eps=income.get("eps"),

            operating_cash_flow=cashflow.get("operatingCashFlow"),

            total_assets=balance.get("totalAssets"),
            total_liabilities=balance.get("totalLiabilities"),
            shareholders_equity=balance.get("totalStockholderEquity"),
        )
