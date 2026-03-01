from fastapi import Request
from fastapi.responses import JSONResponse
from app.core.exceptions import DomainError
from app.core.errors import APIError

def domain_error_handler(request:Request,exc:DomainError):
  status_map = {
    "INVALID_LIMIT":400,
    "INVALID_PERIOD":400,
    "INVALID_SYMBOL":400,
    "FISCALYEAR_MISMATCH":400,
    "ORDERING_VIOLATION":400,
    "SNAPSHOT_NOT_FOUND":400,
    "NO_PEERS_FOUND":404,
    "INSUFFICIENT_DATA":404,
    "EMPTY_DATA":400,
    "NO_FILING_DATE":400,
    "STOCK_NOT_FOUND":404,
    "NOT_ENOUGH_DATA":404,
    "INVALID_FILING_DATE":400,
    "API_KEY_MISSING":401,
    "INVALID_API_KEY":403,
    "FUNDAMENTALS_NOT_FOUND":404,
    "PROVIDER_ERROR":502
  }

  status_code = status_map.get(exc.code)

  return JSONResponse(
    status_code = status_code,
    content = APIError(
      code = exc.code,
      message = exc.message,
      details = exc.details
    ).dict()
  )