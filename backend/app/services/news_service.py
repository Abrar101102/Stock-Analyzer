from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests
from app.core.cache import redis_cache


NEWS_API_URL = "https://newsapi.org/v2/everything"

# Load FinBERT pipeline lazily
_finbert_pipeline = None

def get_finbert_pipeline():
    global _finbert_pipeline
    if _finbert_pipeline is None:
        from transformers import pipeline
        _finbert_pipeline = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    return _finbert_pipeline


POSITIVE_WORDS = {
    "beat",
    "beats",
    "growth",
    "gains",
    "strong",
    "surge",
    "bullish",
    "upgrade",
    "outperform",
    "profit",
    "profits",
    "expansion",
    "optimistic",
    "record",
    "improve",
    "improves",
    "improved",
}

NEGATIVE_WORDS = {
    "miss",
    "misses",
    "decline",
    "drops",
    "drop",
    "fall",
    "falls",
    "bearish",
    "downgrade",
    "underperform",
    "loss",
    "losses",
    "lawsuit",
    "investigation",
    "weak",
    "warning",
    "cut",
    "cuts",
    "slump",
}


@dataclass
class ScoredArticle:
    title: str
    source: str
    url: str
    published_at: str
    description: str
    sentiment_label: str
    sentiment_score: float


class NewsService:
    def __init__(self, api_key: str | None):
        self.api_key = api_key

    @redis_cache(expire_seconds=1800)
    def get_news_and_sentiment(self, symbol: str, limit: int = 10) -> dict[str, Any]:
        if not self.api_key:
            raise ValueError("NEWS_API_KEY is missing. Configure it in backend/app/core/config.py or environment variables.")

        query = self._build_query(symbol)
        payload = self._fetch_news(query=query, limit=limit)

        articles: list[ScoredArticle] = []
        for item in payload.get("articles", []):
            title = (item.get("title") or "").strip()
            description = (item.get("description") or "").strip()
            content_for_scoring = f"{title} {description}".strip()
            score, label = self._score_sentiment(content_for_scoring)

            articles.append(
                ScoredArticle(
                    title=title or "Untitled",
                    source=((item.get("source") or {}).get("name") or "Unknown"),
                    url=(item.get("url") or ""),
                    published_at=(item.get("publishedAt") or ""),
                    description=description,
                    sentiment_label=label,
                    sentiment_score=score,
                )
            )

        aggregate = self._aggregate_sentiment(articles)

        return {
            "symbol": symbol.upper(),
            "query": query,
            "total_results": payload.get("totalResults", 0),
            "overall_sentiment": aggregate["overall_sentiment"],
            "overall_score": aggregate["overall_score"],
            "gauge": aggregate["gauge"],
            "articles": [article.__dict__ for article in articles],
        }

    def _build_query(self, symbol: str) -> str:
        normalized = symbol.upper().strip()
        if normalized == "TCS":
            return "TCS stock OR Tata Consultancy Services"
        return f"{normalized} stock"

    def _fetch_news(self, query: str, limit: int) -> dict[str, Any]:
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": max(1, min(limit, 30)),
            "apiKey": self.api_key,
        }
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        response.raise_for_status()
        payload = response.json()

        if payload.get("status") != "ok":
            message = payload.get("message") or "Unable to fetch news"
            raise ValueError(message)

        return payload

    def _score_sentiment(self, text: str) -> tuple[float, str]:
        if not text:
            return 0.0, "neutral"

        try:
            # truncate text to fit model max length
            text_truncated = text[:1500] 
            pipeline = get_finbert_pipeline()
            result = pipeline(text_truncated)[0]
            
            label = result['label'].lower()
            confidence = result['score']
            
            # Map into our -1.0 to 1.0 score range based on confidence
            if label == "positive":
                score = confidence
            elif label == "negative":
                score = -confidence
            else:
                score = 0.0
                
            return round(score, 3), label
        except Exception:
            return 0.0, "neutral"

    def _label_from_score(self, score: float) -> str:
        if score > 0.1:
            return "positive"
        if score < -0.1:
            return "negative"
        return "neutral"

    def _aggregate_sentiment(self, articles: list[ScoredArticle]) -> dict[str, Any]:
        if not articles:
            return {
                "overall_sentiment": "neutral",
                "overall_score": 0.0,
                "gauge": {"positive": 0, "neutral": 100, "negative": 0},
            }

        scores = [article.sentiment_score for article in articles]
        overall_score = round(sum(scores) / len(scores), 3)
        overall_sentiment = self._label_from_score(overall_score)

        positive_count = sum(1 for article in articles if article.sentiment_label == "positive")
        negative_count = sum(1 for article in articles if article.sentiment_label == "negative")
        neutral_count = len(articles) - positive_count - negative_count

        total = len(articles)
        gauge = {
            "positive": round((positive_count / total) * 100),
            "neutral": round((neutral_count / total) * 100),
            "negative": round((negative_count / total) * 100),
        }

        return {
            "overall_sentiment": overall_sentiment,
            "overall_score": overall_score,
            "gauge": gauge,
        }
