# app/core/lifespan.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from app.db.session import SessionLocal,engine
from app.db.base_class import Base
from app.registry.stock_registry import StockRegistry
from app.data.nifty50_seed import NIFTY50_STOCKS
from app.core.config import settings
from app.services.llm_provider import get_local_llm_provider
import logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup before the app accepts requests.
    Order matters — tables first, then seed.
    """

    # ── 1. Create all tables ───────────────────────────────────────────────
    # Import every model here so SQLAlchemy knows about them before create_all
    from app.models.stock import StockSymbol
    from app.models.technical_indicator import TechnicalIndicator
    from app.models.thesis_cache import ThesisCache
    # add any other models here as your app grows

    logger.info("Creating DB tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables ready.")

    # ── 2. Seed stock registry if empty ───────────────────────────────────
    db = SessionLocal()
    try:
        existing_count = db.query(StockSymbol).count()

        if existing_count == 0:
            logger.info("Stock registry is empty — seeding Nifty50 stocks...")
            seeded = StockRegistry.bulk_seed(db, NIFTY50_STOCKS)
            logger.info(f"Seeded {seeded} stocks into registry.")
        else:
            # ── 3. Sync: add any NEW stocks added to seed file ─────────────
            # This handles the case where you add more stocks to nifty50_seed.py
            # later — they get inserted without wiping existing data
            seed_symbols = {s["symbol"].upper() for s in NIFTY50_STOCKS}
            existing_symbols = {
                row.symbol
                for row in db.query(StockSymbol.symbol).all()
            }
            new_symbols = seed_symbols - existing_symbols

            if new_symbols:
                new_stocks = [
                    s for s in NIFTY50_STOCKS
                    if s["symbol"].upper() in new_symbols
                ]
                added = StockRegistry.bulk_seed(db, new_stocks)
                logger.info(f"Added {added} new stocks from seed file.")
            else:
                logger.info(
                    f"Registry already has {existing_count} stocks — nothing to seed."
                )
    except Exception as e:
        logger.error(f"Startup seeding failed: {e}")
        # Don't crash the app — just log and continue
    finally:
        db.close()

    if settings.LLM_provider == "local":
        try:
            logger.info("Loading local GGUF+LoRA LLM provider...")
            get_local_llm_provider()
            logger.info("Local LLM provider ready.")
        except Exception as e:
            logger.warning(f"Local LLM provider failed to load at startup: {e}")

    yield  # ← app runs here, handling requests

    # ── Shutdown (optional cleanup) ────────────────────────────────────────
    logger.info("App shutting down.")