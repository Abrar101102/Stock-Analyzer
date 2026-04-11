from app.services.thesis_service import ThesisService
from app.services.llm_provider import StubLLMProvider
from app.core.config import settings

def get_thesis_service()->ThesisService:
  llm_provider = None
  if settings.LLM_provider == "gemini" and settings.GEMINI_API_KEY:
    llm_provider = StubLLMProvider()

  return ThesisService(llm_provider = llm_provider)