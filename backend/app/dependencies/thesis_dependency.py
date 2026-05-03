from fastapi import Depends
from sqlalchemy.orm import Session
from app.services.thesis_service import ThesisService
from app.services.llm_provider import StubLLMProvider, get_local_llm_provider, GeminiProvider
from app.services.technical_analysis_service import TechnicalAnalysisService
from app.services.news_service import NewsService
from app.services.valuation_service import ValuationService
from app.services.fundamental_read_service import FundamentalReadService
from app.market_data.base_price_service import BasePriceService
from app.dependencies.db_dependency import get_db
from app.dependencies.news_dependency import get_news_service
from app.core.config import settings

def get_thesis_service(
  db: Session = Depends(get_db),
  news_service: NewsService = Depends(get_news_service),
) -> ThesisService:
  # Select LLM provider
  llm_provider = None
  if settings.LLM_provider == "local":
    try:
      llm_provider = get_local_llm_provider()
    except Exception as e:
      print(f"Local LLM provider unavailable: {e}")
      llm_provider = StubLLMProvider()
  elif settings.LLM_provider == "gemini":
    if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
      try:
        llm_provider = GeminiProvider(api_key=settings.GEMINI_API_KEY)
      except Exception as e:
        print(f"Gemini provider unavailable: {e}")
        llm_provider = StubLLMProvider()
    else:
      llm_provider = StubLLMProvider()
  else:
    llm_provider = StubLLMProvider()

  # Wire all services
  price_service = BasePriceService()
  technical_service = TechnicalAnalysisService()
  valuation_service = ValuationService(price_service)
  fundamental_service = FundamentalReadService()

  return ThesisService(
    llm_provider=llm_provider,
    db=db,
    technical_service=technical_service,
    news_service=news_service,
    valuation_service=valuation_service,
    fundamental_service=fundamental_service,
  )