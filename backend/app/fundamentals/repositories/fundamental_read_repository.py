from sqlalchemy.orm import Session
from app.models.fundamental_snapshot import FundamentalSnapshot
class FundamentalReadRepository:
    
    def get_as_of(self, db, symbol, fiscal_year, as_of_date):
        return (
            db.query(FundamentalSnapshot)
            .filter(
                FundamentalSnapshot.symbol == symbol,
                FundamentalSnapshot.fiscal_year == fiscal_year,
                FundamentalSnapshot.effective_date <= as_of_date
            )
            .order_by(FundamentalSnapshot.effective_date.desc())
            .first()
        )
    
    def get_latest(self, db: Session, symbol: str, fiscal_year: int):
        return (
            db.query(FundamentalSnapshot)
            .filter(
                FundamentalSnapshot.symbol == symbol,
                FundamentalSnapshot.fiscal_year == fiscal_year
            )
            .order_by(FundamentalSnapshot.effective_date.desc())
            .first()
        )
    
    def list_years(self, db: Session, symbol: str):
        return (
            db.query(FundamentalSnapshot.fiscal_year)
            .filter(FundamentalSnapshot.symbol == symbol)
            .distinct()
            .all()
        )
    def get_latest_for_symbol(self,db:Session,symbol:str,limit:int):
        return (
            db.query(FundamentalSnapshot)
            .filter(FundamentalSnapshot.symbol == symbol)
            .order_by(
                FundamentalSnapshot.fiscal_year.desc(),
                FundamentalSnapshot.effective_date.desc()
            )
            .limit(limit)
            .all()
        )
    
    def get_latest_years(self,db:Session,symbol:str,limit:int):
        return (
            db.query(FundamentalSnapshot)
            .filter(FundamentalSnapshot.symbol == symbol)
            .order_by(FundamentalSnapshot.fiscal_year.desc())
            .limit(limit)
            .all()
        )