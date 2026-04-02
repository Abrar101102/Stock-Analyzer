from typing import Optional
from dataclasses import dataclass
from sqlalchemy import Column,String,Boolean,DateTime
from sqlalchemy.sql import func
from app.db.base_class import Base

@dataclass
class StockSymbol(Base):
  __tablename__ = "stock_registry"

  # ── Identity ──────────────────────────────────────────────────────────
  symbol               = Column(String(20),  primary_key=True)  # "TCS"
  exchange             = Column(String(10),  nullable=False, default="NSE")
  yahoo_symbol         = Column(String(30),  nullable=False)     # "TCS.NS"
  alpha_vantage_symbol = Column(String(30),  nullable=False, default="")

  # ── Metadata ──────────────────────────────────────────────────────────
  name                 = Column(String(200), nullable=True)
  sector               = Column(String(100), nullable=True)
  industry             = Column(String(100), nullable=True)

  # ── Index membership flags ────────────────────────────────────────────
  is_nifty50           = Column(Boolean, default=False, nullable=False)
  is_nifty500          = Column(Boolean, default=False, nullable=False)
  is_active            = Column(Boolean, default=True,  nullable=False)

  # ── Audit ─────────────────────────────────────────────────────────────
  created_at           = Column(DateTime, server_default=func.now())
  updated_at           = Column(DateTime, server_default=func.now(), onupdate=func.now())

  def get_symbol_for(self, provider: str) -> str:
    """
    Returns the correct symbol format for a given provider.
    
    Provider → Format mapping:
      yahoo           → RELIANCE.NS
      alpha_vantage   → RELIANCE.BSE
      default         → canonical symbol (RELIANCE)
    """
    mapping = {
      "yahoo": self.yahoo_symbol,
      "alpha_vantage": self.alpha_vantage_symbol or self.yahoo_symbol,
    }
    return mapping.get(provider, self.symbol)
  
  def __repr__(self):
    return f"<StockSymbol {self.symbol} | {self.exchange} | {self.sector}"