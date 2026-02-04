class DomainError(Exception):
  def __init__(self,code:str,message:str,details:dict|None=None):
    self.code = code
    self.message=message
    self.details=details

class NotFoundError(DomainError):
  pass

class ValidationError(DomainError):
  pass

class ProviderError(DomainError):
  pass