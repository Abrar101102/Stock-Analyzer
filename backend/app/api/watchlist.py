from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.session import get_db
from app.models.watchlist import Watchlist
from app.services.thesis_service import ThesisService
from app.services.sector_comparision import SectorComparisionService
from app.services.valuation_service import ValuationService
from app.market_data.base_price_service import BasePriceService
from app.services.trend_service import TrendService

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("/")
def get_watchlist(db: Session = Depends(get_db)):
    items = db.query(Watchlist).order_by(Watchlist.added_at.desc()).all()
    return [{"symbol": item.symbol, "added_at": item.added_at} for item in items]

@router.post("/{symbol}")
def add_to_watchlist(symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper()
    existing = db.query(Watchlist).filter(Watchlist.symbol == symbol).first()
    if existing:
        return {"message": "Symbol already in watchlist", "symbol": symbol}
    
    new_item = Watchlist(symbol=symbol)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return {"message": "Added to watchlist", "symbol": symbol}

@router.delete("/{symbol}")
def remove_from_watchlist(symbol: str, db: Session = Depends(get_db)):
    symbol = symbol.upper()
    existing = db.query(Watchlist).filter(Watchlist.symbol == symbol).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Symbol not found in watchlist")
    
    db.delete(existing)
    db.commit()
    return {"message": "Removed from watchlist"}

from app.dependencies.thesis_dependency import get_thesis_service

@router.get("/compare/all")
def compare_watchlist(
    db: Session = Depends(get_db)
):
    from datetime import datetime, timezone
    from app.models.thesis_cache import ThesisCache
    from app.services.thesis_service import ThesisService
    from app.dependencies.thesis_dependency import get_thesis_service
    
    symbols = [item.symbol for item in db.query(Watchlist).all()]
    if not symbols:
        return []

    # Init services
    price_service = BasePriceService()
    val_service = ValuationService(price_service)
    trend_service = TrendService()
    sector_service = SectorComparisionService(val_service, trend_service)

    # Get cached theses today
    cache_date = datetime.now(timezone.utc).date()
    cached_theses = db.query(ThesisCache).filter(
        ThesisCache.symbol.in_(symbols),
        ThesisCache.date == cache_date
    ).all()
    thesis_map = {th.symbol: th for th in cached_theses}

    results = []
    for sym in symbols:
        comp_data = None
        try:
            comp_model = sector_service.compare_all_metrics(db, sym)
            if comp_model:
                comp_data = comp_model.model_dump() if hasattr(comp_model, "model_dump") else comp_model.dict()
        except Exception:
            pass

        # Try getting thesis cached
        thesis_data = None
        if sym in thesis_map:
            th = thesis_map[sym]
            thesis_data = {
                "symbol": th.symbol,
                "verdict": th.verdict,
                "composite_score": getattr(th, "composite_score", 0),
                "summary": th.summary,
                "signals": getattr(th, "signals", {})
            }

        results.append({
            "symbol": sym,
            "comparison": comp_data,
            "thesis": thesis_data
        })
    
    return results