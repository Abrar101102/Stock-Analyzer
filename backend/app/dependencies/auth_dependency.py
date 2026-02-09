from app.core.exceptions import ValidationError,NotFoundError
from fastapi import Request
import logging
from app.core.api_keys import API_KEYS

logger = logging.getLogger(__name__)

def require_api_key(request:Request):
  api_key = request.headers.get("X-API-Key")

  if not api_key:
    raise NotFoundError(
      code = "API_KEY_MISSING",
      message = "API KEY REQUIRED",
      details = {"recieved":"NO API KEY IN THE HEADER"}
    )
  
  key_data = API_KEYS.get(api_key)

  if not key_data:
    raise ValidationError(
      code = "INVALID_API_KEY",
      message = "INVALID API KEY SENT",
      details = {"recieved":f"{api_key} this is invalid api key provided"}
    )
  logger.info(
    "Authenticated request",
    extra={
        "api_key": api_key[:6] + "***",
        "tier": key_data["tier"],
    }
  )
  
  request.state.api_key = api_key
  request.state.api_tier = key_data["tier"]

def require_pro_key(request:Request):
  require_api_key(request)

  if request.state.api_tier != "pro":
    raise ValidationError(
      code = "INVALID_API_KEY",
      message = "PRO API KEY REQUIRED",
      details = {"recieved":"RECIEVED API KEY SHOULD BE PRO TIER"}
    )