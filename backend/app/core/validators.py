from app.core.exceptions import ValidationError

max_limit = 20

def validate_limit(limit:int)->int:
    if limit <=0:
      raise ValidationError(
        code = "INVALID_LIMIT",
        message = "Limit Must be Greater than Zero",
        details = {"received":limit} 
      )
    if limit > max_limit:
      raise ValidationError(
        code = "INVALID_LIMIT",
        message = f"Limit exceeds maximum allowed value of {max_limit}",
        details = {"received":limit} 
      )
      
    if limit is None:
      raise ValidationError(
        code = "INVALID_LIMIT",
        message = "Limit Must be Provided",
        details = {"received":None} 
      )
    if not isinstance(limit,int):
      raise ValidationError(
        code = "INVALID_LIMIT",
        message = "Limit Must be of Type Integer",
        details = {"received":limit} 
      )
    return limit

def validate_period(period:str):
  allowed_periods = {"annual","quater"}

  if period not in allowed_periods:
    raise ValidationError(
        code = "INVALID_PERIOD",
        message = "The PERIOD SHOULD HAVE BEEN VALID",
        details = {"received" :f"{period} should have been {allowed_periods}"}
      )