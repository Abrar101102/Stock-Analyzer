from fastapi import APIRouter, Depends, Query
from app.dependencies.technical_dependency import get_technical_orchestrator
from app.utils.json_sanitize import sanitize_json_floats
router = APIRouter(prefix="/technical", tags=["Technical Analysis"])


@router.get("/{symbol}/indicators")
def get_technical_indicators(
    symbol: str,
    period: str = Query("1y", description="1mo, 3mo, 6mo, 1y, 2y, 5y"),
    force_refresh: bool = Query(False, description="Force re-fetch from live API"),
    deps=Depends(get_technical_orchestrator),
):
    """
    Full pipeline: fetch price → compute indicators → persist → return.
    
    Uses cached DB data if fresh enough (< 1 day old).
    Pass force_refresh=true to bypass cache.
    """
    result = deps["orchestrator"].get_indicators(
        db=deps["db"],
        symbol=symbol,
        period=period,
        force_refresh=force_refresh,
    )
    return sanitize_json_floats(result)


@router.get("/{symbol}/signals")
def get_signals_only(
    symbol: str,
    period: str = Query("1y"),
    deps=Depends(get_technical_orchestrator),
):
    """Quick endpoint — just the buy/sell signals, minimal data."""
    result = deps["orchestrator"].get_indicators(
        db=deps["db"],
        symbol=symbol,
        period=period,
    )
    return {
        "symbol": symbol,
        "source": result.get("source"),
        "signals": result.get("signals", {}),
    }