from pydantic import BaseModel
from typing import Literal
from datetime import datetime 

class Signal(BaseModel):
  fundamental:str
  technical:str
  sentiment:str
  valuation:str

class ThesisResponseModel(BaseModel):
  symbol:str
  verdict: Literal['Buy','Sell','Hold']
  composite_score: float
  summary:str
  signals: Signal
  generated_at:datetime



