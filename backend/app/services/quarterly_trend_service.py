from app.fundamentals.repositories.quarterly_read_repository import QuarterlyReadReository
from app.core.exceptions import NotFoundError
from sqlalchemy.orm import Session
import json

class QuarterlyTrendService:
  def __init__(self):
    self.quarterly_repo = QuarterlyReadReository()

  def safe_div(self,a,b):
    if a is None or b in (None,0):
      return None
    return a/b

  def get_ttm(self,db:Session,symbol:str,metric_key):
    quarters = self.quarterly_repo.get_last_n_quarters(db,symbol,4)

    if len(quarters) < 4:
      raise NotFoundError(
        code = "INSUFFICIENT_DATA",
        message=f"At least 4 quarters of data required to compute QoQ growth for symbol {symbol}"
      )
    
    total = 0

    for q in quarters:
      data = json.loads(q.data)
      income = data.get("income_statement",{})
      value = income.get(metric_key)

      if value is None:
        return None
      
      total += value

    return total
  
  def get_qoq_growth(self,db:Session,symbol:str,metric_key,offset:int=0):
    quarters = self.quarterly_repo.get_last_n_quarters(db,symbol,offset+2)

    if len(quarters)<2:
      raise NotFoundError(
        code = "INSUFFICIEnt_DATA",
        message=f"At least 2 quarters of data required to calculate QOQ growth for symbol {symbol}"
      )
    
    current = json.loads(quarters[offset].data)
    previous = json.loads(quarters[offset+1].data)

    current_value = current["income_statement"].get(metric_key)
    previous_value = previous["income_statement"].get(metric_key)

    growth = self.safe_div(current_value - previous_value if current_value and previous_value else None ,previous_value)

    return growth * 100 if growth is not None else None
  
  def get_yoy_growth(self,db:Session,symbol:str,metric_key):
    quarters = self.quarterly_repo.get_last_n_quaters(db,symbol,5)

    if len(quarters) < 5:
      raise NotFoundError(
        code = "INSUFFICIENT_DATA",
        message= f"Atleast 5 quarters required for YoY growth"
      )
    
    current = quarters[0].data.get("income_statement",{})
    last_year_same_q = quarters[4].get("income_statement",{})

    current_value = current.get(metric_key)
    last_year_value= last_year_same_q.get(metric_key)

    growth = self.safe_div(current_value - last_year_value if current_value is not None and last_year_value is not None else None,last_year_value)

    return growth * 100 if growth is not None  else None
  
  def get_earning_acceleration(self,db:Session,symbol:str,metric_key):
    current_qoq = self.get_qoq_growth(db,symbol,metric_key,offset=0)
    previous_qoq = self.get_qoq_growth(db,symbol,metric_key,offset=1)

    if current_qoq is None or previous_qoq is None:
      return None
    
    return current_qoq - previous_qoq
  
  def get_momentum_score(self,db:Session,symbol,metric_key):
    yoy=self.get_yoy_growth(db,symbol,metric_key)
    qoq = self.get_qoq_growth(db,symbol,metric_key)
    acceleration = self.get_earning_acceleration(db,symbol,metric_key)

    if None in (yoy,qoq,acceleration):
      return None
    
    score = (yoy *0.5) + (qoq*0.3) + (acceleration*0.2)

    return round(score,2)
  
  def build_quarterly_snapshot(self, db: Session, symbol: str):

    return {
        "symbol": symbol,
        "revenue": {
            "ttm": self.get_ttm(db, symbol, "revenue"),
            "qoq_growth": self.get_qoq_growth(db, symbol, "revenue"),
            "yoy_growth": self.get_yoy_growth(db, symbol, "revenue"),
            "acceleration": self.get_earnings_acceleration(db, symbol, "revenue"),
        },
        "eps": {
            "ttm": self.get_ttm(db, symbol, "eps"),
            "qoq_growth": self.get_qoq_growth(db, symbol, "eps"),
            "yoy_growth": self.get_yoy_growth(db, symbol, "eps"),
            "acceleration": self.get_earnings_acceleration(db, symbol, "eps"),
        },
        "ebitda": {
            "ttm": self.get_ttm(db, symbol, "ebitda"),
            "qoq_growth": self.get_qoq_growth(db, symbol, "ebitda"),
            "yoy_growth": self.get_yoy_growth(db, symbol, "ebitda"),
            "acceleration": self.get_earnings_acceleration(db, symbol, "ebitda"),
        }
    }
