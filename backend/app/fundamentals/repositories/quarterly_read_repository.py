from app.models.quarterly_snapshot_model import QuarterlyFundamentalSnapshot
from sqlalchemy.orm import Session

class QuarterlyReadReository:
  def get_last_n_quaters(self,db:Session,symbol:str,limit:int=5):
    return (
      db.query(QuarterlyFundamentalSnapshot)
      .filter(QuarterlyFundamentalSnapshot.symbol == symbol)
      .order_by(QuarterlyFundamentalSnapshot.fiscal_year.desc(),
                QuarterlyFundamentalSnapshot.fiscal_quater.desc()
      )
      .limit(limit)
      .all()
    )  
  def get_quater(self,db:Session,symbol:str,fiscal_year:int,fiscal_quater:int):
    return (
      db.query(QuarterlyFundamentalSnapshot)
      .filter(QuarterlyFundamentalSnapshot.symbol == symbol,
              QuarterlyFundamentalSnapshot.fiscal_year == fiscal_year,
              QuarterlyFundamentalSnapshot.fiscal_quater == fiscal_quater
      )
      .first()
    )
  def get_as_of(self,db:Session,symbol:str,date):
    return (
      db.query(QuarterlyFundamentalSnapshot)
      .filter(QuarterlyFundamentalSnapshot.symbol == symbol,
              QuarterlyFundamentalSnapshot.effective_date <= date
      )
      .order_by(QuarterlyFundamentalSnapshot.effective_date.desc())
      .first()
    )