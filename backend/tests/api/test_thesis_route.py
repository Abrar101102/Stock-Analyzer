from datetime import datetime,timezone
from backend.app.models.response.thesis_model import ThesisResponseModel
import pytest

def test_thesis_response_model():
  payload = {
    "symbol":"TCS",
    "verdict":"Hold",
    "summary":"Tcs shows Good Fundamentals",
    "signals":{
      "fundamental":"posetive",
      "technical":"neutral",
      "sentiment":"posetive",
      "valuation":"neutral"
    },
    "generated_at":datetime.now(timezone.utc)
  }

  obj = ThesisResponseModel(**payload)

  assert obj.symbol == "TCS"
  assert obj.verdict == "Hold"