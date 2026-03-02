from sqlalchemy.orm import Session
from app.valuation.models.valuation_model import ValuationResponse
from app.fundamentals.repositories.fundamental_read_repository import FundamentalReadRepository
from app.services.quarterly_trend_service import QuarterlyTrendService
from app.core.exceptions import NotFoundError
from app.market_data.base_price_service import BasePriceService
import json


class ValuationService:
  def __init__(self,price_service:BasePriceService):
    self.fundamental_repo = FundamentalReadRepository()
    self.price_service = price_service
    self.quarterly_service = QuarterlyTrendService()

  #Internal method to compute various metrics, can be extended in future for more complex calculations or to fetch additional data as needed
  def _compute_metrics(self,db:Session,symbol:str):
    snapshot = self.fundamental_repo.get_latest_snapshot_for_symbol(db,symbol)

    if not snapshot:
      raise NotFoundError(
        code = "SNAPSHOT_NOT_FOUND",
        message=f"No fundamental snapshot found for symbol {symbol}"
      )
    
    data = json.loads(snapshot.data)

    income = data.get("income_statement",{})
    balance = data.get("balance_sheet",{})
    cash_flow = data.get("cash_flow_statement",{})

    eps = self.quarterly_service.get_ttm(db,symbol,"eps")
    net_income = income.get("net_income")
    ebitda = income.get("ebitda")

    total_debt = balance.get("total_debt")
    cash = balance.get("cash_and_equivalents")
    equity = balance.get("shareholders_equity")
    share_outstanding = balance.get("share_outstanding")

    price = self.price_service.get_latest_price(symbol)

    def safe_div(a,b):
      if a is None or b is None or b == 0:
        return None
      return a/b
    
    market_cap = price * share_outstanding
    pe_ratio = safe_div(price,eps)
    ev = None
    if market_cap is not None and total_debt is not None and cash is not None:
      ev = market_cap + total_debt - cash
    
    ev_ebitda = safe_div(ev,ebitda)

    book_value_per_share = safe_div(equity,share_outstanding)
    price_to_book = safe_div(price,book_value_per_share)

    return {
      "price": price,
      "pe_ratio": pe_ratio,
      "ev": ev,
      "ev_ebitda": ev_ebitda,
      "book_value_per_share": book_value_per_share,
      "price_to_book": price_to_book
    }
  
  def get_pe_ratio(self,db:Session,symbol:str):
    metrics = self._compute_metrics(db,symbol)
    return round(metrics["pe_ratio"],2) if metrics["pe_ratio"] else None
  
  def get_ev_ebitda(self,db:Session,symbol:str):
    metrics = self._compute_metrics(db,symbol)
    return round(metrics["ev_ebitda"],2) if metrics["ev_ebitda"] else None
  
  def get_price_to_book(self,db:Session,symbol:str):
    metrics = self._compute_metrics(db,symbol)
    return round(metrics["price_to_book"],2) if metrics["price_to_book"] else None

  def get_valuation(self,db:Session,symbol:str)->ValuationResponse:
    snapshot = self.fundamental_repo.get_latest_snapshot_for_symbol(db,symbol)

    if not snapshot:
      raise NotFoundError(
        code="SNAPSHOT_NOT_FOUND",
        message=f"No fundamental snapshot found for symbol {symbol}"
      )
    
    data = json.loads(snapshot.data)

    income = data.get("income_statement",{})
    balance = data.get("balance_sheet",{})
    cash_flow = data.get("cash_flow_statement",{})

    
    eps = self.quarterly_service.get_ttm(db,symbol,"eps")
    net_income = income.get("net_income")
    ebitda = income.get("ebitda")

    total_debt = balance.get("total_debt")
    cash = balance.get("cash_and_equivalents")
    equity = balance.get("shareholders_equity")
    share_outstanding = balance.get("share_outstanding")

    price = self.price_service.get_latest_price(symbol)

    def safe_div(a,b):
      if a is None or b is None or b == 0:
        return None
      return a/b
    
    market_cap = price * share_outstanding
    pe_ratio = safe_div(price,eps)
    ev = None
    if market_cap is not None and total_debt is not None and cash is not None:
      ev = market_cap + total_debt - cash
    
    ev_ebitda = safe_div(ev,ebitda)

    book_value_per_share = safe_div(equity,share_outstanding)
    price_to_book = safe_div(price,book_value_per_share)

    return ValuationResponse(
      symbol = symbol,
      price= round(price,2),
      pe_ratio= round(pe_ratio,2) if pe_ratio is not None else None,
      ev= round(ev,2) if ev is not None else None,
      ev_ebitda= round(ev_ebitda,2) if ev_ebitda is not None else None,
      book_value_per_share= round(book_value_per_share,2) if book_value_per_share is not None else None,
      price_to_book= round(price_to_book,2) if price_to_book is not None else None
    )