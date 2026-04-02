# app/services/stock_registry.py
from sqlalchemy.orm import Session
from app.models.stock import StockSymbol
from app.core.exceptions import NotFoundError
from typing import Dict, List, Optional
import logging
import time

logger = logging.getLogger(__name__)


class StockRegistry:
    """
    DB-backed registry with 5-minute in-memory cache.
    DB is source of truth. Cache avoids hitting DB on every request.
    """
    _cache: Dict[str, StockSymbol] = {}
    _cache_ts: float = 0.0
    CACHE_TTL = 300  # 5 minutes

    # ── Read ──────────────────────────────────────────────────────────────

    @classmethod
    def get_stock(cls, symbol: str, db: Session) -> StockSymbol:
        normalized = symbol.upper().strip()
        cls._refresh_cache_if_stale(db)
        stock = cls._cache.get(normalized)
        if not stock:
            raise NotFoundError(
                code="STOCK_NOT_FOUND",
                message=f"'{symbol}' not found. Add it via POST /api/registry/stocks"
            )
        return stock

    @classmethod
    def exists(cls, symbol: str, db: Session) -> bool:
        cls._refresh_cache_if_stale(db)
        return symbol.upper().strip() in cls._cache

    @classmethod
    def list_all(cls, db: Session) -> List[StockSymbol]:
        cls._refresh_cache_if_stale(db)
        return list(cls._cache.values())

    @classmethod
    def get_by_sector(cls, sector: str, db: Session) -> List[StockSymbol]:
        cls._refresh_cache_if_stale(db)
        return [
            s for s in cls._cache.values()
            if s.sector and s.sector.lower() == sector.lower()
        ]

    @classmethod
    def get_peers(cls, symbol: str, db: Session) -> List[StockSymbol]:
        stock = cls.get_stock(symbol, db)
        return [
            s for s in cls.get_by_sector(stock.sector, db)
            if s.symbol != symbol
        ]

    # ── Write ─────────────────────────────────────────────────────────────

    @classmethod
    def add_stock(
        cls,
        db: Session,
        symbol: str,
        name: str = "",
        sector: str = "",
        industry: str = "",
        exchange: str = "NSE",
        is_nifty50: bool = False,
        is_nifty500: bool = False,
    ) -> StockSymbol:
        normalized = symbol.upper().strip()

        # Auto-derive provider symbols from exchange
        yahoo_suffix = ".NS" if exchange == "NSE" else ".BO"
        av_suffix    = ".NSE" if exchange == "NSE" else ".BSE"

        stock = StockSymbol(
            symbol               = normalized,
            exchange             = exchange,
            yahoo_symbol         = f"{normalized}{yahoo_suffix}",
            alpha_vantage_symbol = f"{normalized}{av_suffix}",
            name                 = name or normalized,
            sector               = sector or None,
            industry             = industry or None,
            is_nifty50           = is_nifty50,
            is_nifty500          = is_nifty500,
            is_active            = True,
        )
        db.merge(stock)   # upsert — safe to re-run on restarts
        db.commit()
        cls._invalidate_cache()
        logger.info(f"Registered: {normalized} ({exchange})")
        return stock

    @classmethod
    def bulk_seed(cls, db: Session, stocks: List[dict]) -> int:
        """Seed a list of stock dicts. Safe to call multiple times."""
        count = 0
        for s in stocks:
            cls.add_stock(db, **s)
            count += 1
        logger.info(f"Seeded {count} stocks")
        return count

    # ── Cache internals ───────────────────────────────────────────────────

    @classmethod
    def _refresh_cache_if_stale(cls, db: Session):
        if time.time() - cls._cache_ts < cls.CACHE_TTL:
            return
        rows = (
            db.query(StockSymbol)
            .filter(StockSymbol.is_active == True)
            .all()
        )
        cls._cache = {r.symbol: r for r in rows}
        cls._cache_ts = time.time()
        logger.debug(f"Cache refreshed: {len(cls._cache)} stocks loaded")

    @classmethod
    def _invalidate_cache(cls):
        cls._cache_ts = 0.0