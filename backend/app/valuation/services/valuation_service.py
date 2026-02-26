from sqlalchemy.orm import session
from app.valuation.models.valuation_model import ValuationResponse
from app.fundamentals.repositories.fundamental_read_repository import FundamentalReadRepository
from app.core.exceptions import NotFoundError
from app.market_data.base_price_service import BasePriceService
import json

class ValuationService:
  def __init__(self,price_service:BasePriceService):
    self.fundamental_repo = FundamentalReadRepository()
    self.price_service = price_service
  def get_valuation(self,db:session,symbol:str)->ValuationResponse:
    snapshot = self.fundamental_repo.get_la(db,symbol)

    if not snapshot:
      raise NotFoundError(
        code="SNAPSHOT_NOT_FOUND",
        message=f"No fundamental snapshot found for symbol {symbol}"
      )
    
    data = json.loads(snapshot.data)

    income = data.get("income_statement",{})
    balance = data.get("balance_sheet",{})
    cash_flow = data.get("cash_flow_statement",{})

    eps = income.get("eps")
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