from sqlalchemy.orm import Session
from typing import List
from app.fundamentals.repositories.fundamental_read_repository import FundamentalReadRepository
from app.fundamentals.models.trend_model import TrendResponse,YearTrend
from app.core.exceptions import NotFoundError
from app.core.logging import trace
import json

class TrendService:
  def __init__(self):
    self.repository = FundamentalReadRepository()
  
  @trace
  def get_trends(self,db:Session,symbol:str,limit:int=5)->TrendResponse:
    snapshots = self.repository.get_latest_years(db=db,symbol=symbol,limit=limit)

    snapshots = sorted(snapshots,key = lambda x:x.fiscal_year)

    years_data :List[YearTrend] = []

    prev_revenue = None 
    prev_net_income = None
    prev_eps = None

    for entity in snapshots:
      data = json.loads(entity.data or "{}")

      income = data.get("income_statement",{})
      balance_sheet = data.get("balance_sheet",{})
      
      revenue = income.get("total_revenue")
      net_income = income.get("net_income")
      equity = balance_sheet.get("shareholders_equity")
      eps = income.get("eps")

      #safe div
      def safe_div(a,b):
        try:
          return a/b if a is not None and b is not None and b != 0 else None
        except Exception as e:
          return None
      
      revenue_growth = safe_div(revenue - prev_revenue,abs(prev_revenue)) if prev_revenue else None
      net_income_growth = safe_div(net_income - prev_net_income,abs(prev_net_income)) if prev_net_income else None
      eps_growth = safe_div(eps - prev_eps,abs(prev_eps)) if prev_eps is not None else None
      roe = safe_div(net_income,equity)

      years_data.append(
        YearTrend(
          fiscal_year = entity.fiscal_year,
          revenue = revenue,
          revenue_growth=round(revenue_growth,4) if revenue_growth is not None else None,
          net_income = net_income,
          net_income_growth = round(net_income_growth,4) if net_income_growth is not None else None,
          eps = eps,
          eps_growth = round(eps_growth,4) if eps_growth is not None else None,
          roe = round(roe,4) if roe else None
        )
      )

      prev_revenue = revenue
      prev_net_income = net_income
      prev_eps = eps

    cagr_3yr = self.calcultate_cagr(snapshots,3)
    cagr_5yr = self.calcultate_cagr(snapshots,5)
    
    return TrendResponse(
      symbol = symbol,
      years = years_data,
      cagr_3yr = cagr_3yr,
      cagr_5yr = cagr_5yr
    )
  # @staticmethod
  @trace
  def calcultate_cagr(self,snapshots:List,years:int):
    if len(snapshots) < years+1:
      raise NotFoundError(
        code="NOT_ENOUGH_DATA",
        message=f"Not enough data to calculate CAGR. At least {years+1} years of data are required."
      )
      
    start = json.loads(snapshots)[-(years+1)].data.get('revenue')
    end = json.loads(snapshots)[-1].data.get("revenue")

    if not start or not end or start == 0:
      raise NotFoundError(
          code="NOT_ENOUGH_DATA",
          message=f"Revenue data is missing or invalid for CAGR calculation."
        )
    n= years
    cagr = (end/start)**(1/n) - 1

    return round(cagr,4)