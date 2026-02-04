from pydantic import BaseModel
from typing import Optional,Dict,Any

class APIError(BaseModel):
  code:str
  message:str
  details:Optional[Dict[str,Any]]=None


  ## Example
# {
#   "code": "INVALID_LIMIT",
#   "message": "Limit must be a positive integer",
#   "details": {
#     "received": -3
#   }
# }