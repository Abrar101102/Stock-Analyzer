from sqlalchemy.orm import Session
from typing import List
from app.fundamentals.repositories.fundamental_read_repository import FundamentalReadRepository
from app.fundamentals.models.financial_ratio_model import FinancialRatioModel
import json
class DerivedMetricsService:

  def __init__(self):
    self.repository = FundamentalReadRepository()
      
  def get_ratios(self,db:Session,symbol:str,limit:int=5) -> List[FinancialRatioModel]:

    snapshots= self.repository.get_latest_for_symbol(db,symbol,limit)

    ratios = []

    for entity in snapshots:
      data = json.loads(entity.data or "{}")

      income = data.get("income_statement",{})
      balance_sheet = data.get("balance_sheet",{})
      cashflow = data.get("cash_flow_statement",{})

      net_income = income.get("net_income")
      revenue = income.get("total_revenue")

      current_assets = balance_sheet.get("current_assets")
      current_liabilities = balance_sheet.get("current_liabilities")
      total_liabilities = balance_sheet.get("total_liabilities")
      equity = balance_sheet.get("shareholders_equity")

      ocf = cashflow.get("operating_cash_flow")
      capex = cashflow.get("capital_expenditure")

      def safe_div(a,b):
        try:
          return a/b if a is not None and b is not None and b != 0 else None
        except:
          return None
      
      net_margin = safe_div(net_income,revenue)
      current_ratio = safe_div(current_assets,current_liabilities)
      debt_to_equity = safe_div(total_liabilities,equity)

      ocf_quality = safe_div(ocf,abs(net_income)) if net_income else None
      free_cash_flow = ocf -abs(capex) if ocf and capex else None

      ratios.append(
        FinancialRatioModel(
          symbol= entity.symbol,
          fiscal_year = entity.fiscal_year,
          net_margin= round(net_margin,4) if net_margin else None,
          current_ratio = round(current_ratio,4) if current_ratio else None,
          debt_to_equity = round(debt_to_equity,4) if debt_to_equity else None,
          ocf_quality = round(ocf_quality,4) if ocf_quality else None,
          free_cash_flow = round(free_cash_flow,4) if free_cash_flow else None
        )
      )
    
    return ratios
