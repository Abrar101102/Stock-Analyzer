from datetime import datetime, timezone
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.dependencies.thesis_dependency import get_thesis_service
from app.dependencies.db_dependency import get_db
from app.services.thesis_service import ThesisService
from app.models.thesis_cache import ThesisCache
from app.models.response.thesis_model import ThesisResponseModel
from app.core.logging import trace

@trace
def _score_to_confidence(score: float) -> str:
    
    if score >= 80:
        return "High"
    elif score >= 50:
        return "Medium"
    return "Low"


router = APIRouter(prefix="/thesis",tags = ["thesis"])

@router.get("/{symbol}")
@trace
def get_thesis(symbol:str,service:ThesisService = Depends(get_thesis_service),db:Session = Depends(get_db)):
  if not symbol.isalpha() or len(symbol)> 10:
    raise HTTPException(status_code = 400,detail = "Invalid Symbol")
  normalized_symbol = symbol.upper()
  cache_date = datetime.now(timezone.utc).date()
  cached = db.query(ThesisCache).filter(
    ThesisCache.symbol == normalized_symbol,
    ThesisCache.date == cache_date,
  ).first()

  if cached:
    return ThesisResponseModel(
      symbol=cached.symbol,
      verdict=cached.verdict,
      composite_score=cached.composite_score,
      summary=cached.summary,
      signals=cached.signals,
      generated_at=cached.generated_at,
      confidence=_score_to_confidence(cached.composite_score)
    )

  response = service.generate(normalized_symbol)
  payload = response.dict()
  existing = db.query(ThesisCache).filter(
    ThesisCache.symbol == normalized_symbol,
    ThesisCache.date == cache_date,
  ).first()

  if existing:
    existing.verdict = payload["verdict"]
    existing.composite_score = payload["composite_score"]
    existing.summary = payload["summary"]
    existing.signals = payload["signals"]
    existing.generated_at = payload["generated_at"]
  else:
    db.add(ThesisCache(
      symbol=normalized_symbol,
      date=cache_date,
      verdict=payload["verdict"],
      composite_score=payload["composite_score"],
      summary=payload["summary"],
      signals=payload["signals"],
      generated_at=payload["generated_at"],
      # confidence=_score_to_confidence(payload['composite_score'])
    ))

  db.commit()
  return response