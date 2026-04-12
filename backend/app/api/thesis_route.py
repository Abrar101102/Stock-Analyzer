from fastapi import APIRouter,Depends,HTTPException
from app.dependencies.thesis_dependency import get_thesis_service
from app.services.thesis_service import ThesisService

router = APIRouter("/thesis",tags = ["thesis"])

@router.get("/{symbol}")
def get_thesis(symbol:str,service:ThesisService = Depends(get_thesis_service)):
  if not symbol.isalpha() or len(symbol)> 10:
    raise HTTPException(status_code = 400,detail = "Invalid Symbol")
  return service.generate(symbol)