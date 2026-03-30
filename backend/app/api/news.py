from fastapi import APIRouter, Depends, HTTPException, Query
import requests

from app.dependencies.news_dependency import get_news_service
from app.services.news_service import NewsService


router = APIRouter(prefix="/news", tags=["News"])


@router.get("/{symbol}")
def get_news_for_symbol(
    symbol: str,
    limit: int = Query(10, ge=1, le=30),
    news_service: NewsService = Depends(get_news_service),
):
    try:
        return news_service.get_news_and_sentiment(symbol=symbol, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch news from provider") from exc
