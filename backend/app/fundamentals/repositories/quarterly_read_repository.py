from backend.app.models.quarterly_snapshot_model import QuarterlyFundamentalSnapshot
from sqlalchemy.orm import Session

class QuarterlyReadReository:
  def get_last_n_quaters(self,db:Session,symbol:str,limit:int=5):
    return (
      db.query(QuaterlyFundamentalSnapshot)
      .filter(QuaterlyFundamentalSnapshot.symbol == symbol)
      .order_by(QuaterlyFundamentalSnapshot.fiscal_year.desc(),
                QuaterlyFundamentalSnapshot.fiscal_quater.desc()
      )
      .limit(limit)
      .all()
    )  
  def get_quater(self,db:Session,symbol:str,fiscal_year:int,fiscal_quater:int):
    return (
      db.query(QuaterlyFundamentalSnapshot)
      .filter(QuaterlyFundamentalSnapshot.symbol == symbol,
              QuaterlyFundamentalSnapshot.fiscal_year == fiscal_year,
              QuaterlyFundamentalSnapshot.fiscal_quater == fiscal_quater
      )
      .first()
    )
  def get_as_of(self,db:Session,symbol:str,date):
    return (
      db.query(QuaterlyFundamentalSnapshot)
      .filter(QuaterlyFundamentalSnapshot.symbol == symbol,
              QuaterlyFundamentalSnapshot.effective_date <= date
      )
      .order_by(QuaterlyFundamentalSnapshot.effective_date.desc())
      .first()
    )