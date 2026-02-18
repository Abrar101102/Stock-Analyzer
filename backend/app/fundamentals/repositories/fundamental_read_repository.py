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