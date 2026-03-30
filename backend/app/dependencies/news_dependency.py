from app.core.config import NEWS_API_KEY
from app.services.news_service import NewsService


def get_news_service() -> NewsService:
    return NewsService(api_key=NEWS_API_KEY)
