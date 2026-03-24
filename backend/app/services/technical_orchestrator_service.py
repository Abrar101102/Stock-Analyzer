from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.technical_persistance import TechnicalPersistanceService
from app.services.stock_service import StockService
from app.data_providers.base_provider import MarketDataProvider
from sqlalchemy.orm import Session
from app.models.technical_indicator import TechnicalIndicator
from datetime import date, timedelta
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)


class TechnicalOrchestratorService:
    """
    Orchestrates the full pipeline:
      fetch price → compute indicators → persist → return
    
    This is the GLUE between your live API providers and your DB.
    """

    def __init__(
        self,
        stock_service: StockService,
        analysis_service: TechnicalAnalysisService,
        persistence_service: TechnicalPersistanceService,
    ):
        self.stock_service = stock_service
        self.analysis = analysis_service
        self.persistence = persistence_service

    def get_indicators(
        self,
        db: Session,
        symbol: str,
        period: str = "1y",
        force_refresh: bool = False,
        staleness_days: int = 1,
    ) -> Dict:
        """
        Main entry point. 
        
        1. Check DB for fresh data (skip API call if recent enough)
        2. If stale/empty → fetch live price data → compute → persist
        3. Return indicators + signals
        """

        # ─── STEP 1: Check if we have fresh data in DB ───
        if not force_refresh:
            cached = self._get_cached_indicators(db, symbol, staleness_days)
            if cached:
                logger.info(f"Returning cached indicators for {symbol}")
                return self._format_response(symbol, period, cached)

        # ─── STEP 2: Fetch live OHLCV price data from provider ───
        logger.info(f"Fetching live price data for {symbol} (period={period})")
        price_data = self.stock_service.get_price_history(symbol, period)

        if not price_data:
            return {
                "symbol": symbol,
                "period": period,
                "error": "No price data available from any provider",
                "data": [],
                "signals": {},
            }

        # ─── STEP 3: Compute all technical indicators ───
        df = self.analysis.compute_indicators(price_data)

        # ─── STEP 4: Persist computed indicators to PostgreSQL ───
        self.persistence.persist_indicators(symbol, df)

        # ─── STEP 5: Return formatted response ───
        signals = self.analysis.get_signals(df)

        return {
            "symbol": symbol,
            "period": period,
            "count": len(df),
            "source": "live_computed",
            "data": df.to_dict(orient="records"),
            "signals": signals,
        }

    def _get_cached_indicators(self, db: Session, symbol: str, staleness_days:int) -> Optional[List]:
        """
        Two-step check:
        1. Is our data fresh? (check if latest row is within staleness_days)
        2. If yes, return the FULL history (up to 500 rows), not just recent rows.
        """
        cutoff_date = date.today() - timedelta(days=staleness_days)

        # Step 1: Check freshness — does a recent row exist?
        latest_row = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.symbol == symbol)
            .order_by(TechnicalIndicator.date.desc())
            .first()
        )

        if not latest_row:
            return None  # No data at all → fetch live

        if latest_row.date < cutoff_date:
            return None  # Data is stale → fetch live

        # Step 2: Data is fresh — return FULL history for charting
        rows = (
            db.query(TechnicalIndicator)
            .filter(TechnicalIndicator.symbol == symbol)
            .order_by(TechnicalIndicator.date.asc())   # oldest → newest for chart
            .limit(500)
            .all()
        )

        return rows if rows else None

    def _format_response(self, symbol: str, period: str, rows: List) -> Dict:
        """Format DB rows into API response."""
        data = []
        for row in reversed(rows):  # oldest first
            data.append({
                "date": str(row.date),
                "sma_20": row.sma_20,
                "sma_50": row.sma_50,
                "sma_200": row.sma_200,
                "ema_12": row.ema_12,
                "ema_26": row.ema_26,
                "rsi_14": row.rsi_14,
                "macd_line": row.macd_line,
                "macd_signal": row.macd_signal,
                "macd_histogram": row.macd_histogram,
                "bb_upper": row.bb_upper,
                "bb_middle": row.bb_middle,
                "bb_lower": row.bb_lower,
                "vwap": row.vwap,
                "support_level": row.support_level,
                "resistance_level": row.resistance_level,
            })

        # Compute signals from latest cached data
        latest = rows[-1]
        signals = {}
        if latest.rsi_14 is not None:
            signals["rsi"] = (
                "oversold" if latest.rsi_14 < 30
                else "overbought" if latest.rsi_14 > 70
                else "neutral"
            )
        if latest.macd_histogram is not None:
            signals["macd"] = "bullish" if latest.macd_histogram > 0 else "bearish"

        return {
            "symbol": symbol,
            "period": period,
            "count": len(data),
            "source": "cached",
            "data": data,
            "signals": signals,
        }