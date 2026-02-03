from app.api.v1.schemas import FundamentalSnapshotV1
from app.api.v1.schemas import IncomeStatementV1
from app.api.v1.schemas import BalanceSheetV1
from app.api.v1.schemas import CashFlowV1
from app.api.v1.schemas import RatioV1

from app.fundamentals.models.fundamental_snapshot_model import FundamentalSnapshotModel
from app.fundamentals.models.income_statement_model import IncomeStatementModel
from app.fundamentals.models.balance_sheet_model import BalanceSheetModel
from app.fundamentals.models.cash_flow_model import CashFlowStatementModel
from app.fundamentals.models.financial_ratio_model import FinancialRatioModel

def snapshot_to_v1(snapshot:FundamentalSnapshotModel)->FundamentalSnapshotV1:
  return FundamentalSnapshotV1(
    symbol=snapshot.symbol,
    fiscal_year=snapshot.fiscal_year,
    period=snapshot.period,
    total_revenue=snapshot.total_revenue,
    net_income=snapshot.net_income,
    eps=snapshot.eps,
    operating_cash_flow=snapshot.operating_cash_flow,
    total_assets=snapshot.total_assets,
    total_liabilities=snapshot.total_liabilities,
    shareholders_equity=snapshot.shareholders_equity
  )

def income_statement_to_v1(incomestatement:IncomeStatementModel)->IncomeStatementV1:
  return IncomeStatementV1(
    symbol=incomestatement.symbol,
    fiscal_year=incomestatement.fiscal_year,
    period=incomestatement.fiscal_year,
    total_revenue=incomestatement.total_revenue,
    operating_income=incomestatement.operating_income,
    net_income=incomestatement.net_income,
    eps=incomestatement.eps
  )

def balance_sheet_to_v1(balancesheet:BalanceSheetModel)->BalanceSheetV1:
  return BalanceSheetV1(
    symbol=balancesheet.symbol,
    fiscal_year=balancesheet.fiscal_year,
    period=balancesheet.period,
    total_assets=balancesheet.total_assets,
    current_assets=balancesheet.current_assets,
    cash_and_equivalents=balancesheet.cash_and_equivalents,
    total_liabilities=balancesheet.total_liabilities,
    current_liabilities=balancesheet.current_liabilities,
    long_term_debt=balancesheet.long_term_debt,
    shareholders_equity=balancesheet.shareholders_equity
  )

def cash_flow_to_v1(cashflow:CashFlowStatementModel)->CashFlowV1:
  return CashFlowV1(
    symbol=cashflow.symbol,
    fiscal_year=cashflow.fiscal_year,
    period=cashflow.fiscal_year,
    operating_cash_flow=cashflow.operating_cash_flow,
    capital_expenditure=cashflow.capital_expenditure,
    investing_cash_flow=cashflow.investing_cash_flow,
    financial_cash_flow=cashflow.financing_cash_flow,
    net_cash_flow=cashflow.net_cash_flow
  )

def ratio_to_v1(financialratio:FinancialRatioModel)->RatioV1:
  return RatioV1(
    symbol=financialratio.symbol,
    fiscal_year=financialratio.fiscal_year,
    net_margin=financialratio.net_margin,
    current_ratio=financialratio.current_ratio,
    debt_to_equity=financialratio.debt_to_equity,
    ofc_quality=financialratio.ocf_quality,
    free_cash_flow=financialratio.free_cash_flow
  )