from sqlalchemy.orm import Session
from app.models.technical_indicator import TechnicalIndicator
from sqlalchemy.dialects.postgresql import insert
from app.utils.sanitize import sanitize_value
from app.db.session import SessionLocal
from app.core.logging import trace
from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class TechnicalPersistanceService:
    """Saves computed technical indicators to PostgreSQL."""
    INDICATOR_COLS = [
        'sma_20', 'sma_50', 'sma_200', 'ema_12', 'ema_26',
        'rsi_14', 'macd_line', 'macd_signal', 'macd_histogram',
        'bb_upper', 'bb_middle', 'bb_lower', 'vwap',
        'support_level', 'resistance_level'
    ]

    @trace
    def persist_indicators(self, symbol: str, df: pd.DataFrame):
        session: Session = SessionLocal()
        try:
            rows_saved = 0
            for _, row in df.iterrows():
                if row.get('date') is None:
                    continue

                existing = session.query(TechnicalIndicator).filter_by(
                    symbol=symbol,
                    date=row['date'].date() if hasattr(row['date'], 'date') else row['date']
                ).first()

                if existing:
                    # Update existing record
                    for col in self.INDICATOR_COLS:
                        setattr(existing, col, sanitize_value(row.get(col)))
                    existing.computed_at = datetime.utcnow()
                else:
                    row_date = row['date'].date() if hasattr(row['date'], 'date') else row['date']
                    payload = {
                        "symbol":symbol,
                        "date": row_date,
                        "computed_at": datetime.utcnow(),
                        **{col: sanitize_value(row.get(col)) for col in self.INDICATOR_COLS}
                    }
                    stmt = insert(TechnicalIndicator).values(**payload)
                    stmt = stmt.on_conflict_do_update(
                    index_elements= [TechnicalIndicator.symbol,TechnicalIndicator.date],
                    set_={
                        **{col:payload[col] for col in self.INDICATOR_COLS},
                        "computed_at":payload["computed_at"]
                    },
                    )
                    session.execute(stmt)
                    rows_saved += 1

            session.commit()
            logger.info(f"Persisted {rows_saved} indicator rows for {symbol}")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to persist indicators for {symbol}: {e}")
            raise
        finally:
            session.close()