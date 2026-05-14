from sqlalchemy import Column, String, DateTime
from datetime import datetime, timezone
from app.db.base_class import Base

class Watchlist(Base):
    __tablename__ = "watchlist"
    symbol = Column(String, primary_key=True, index=True)
    added_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
