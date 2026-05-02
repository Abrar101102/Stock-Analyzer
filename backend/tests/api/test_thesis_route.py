from datetime import datetime,timezone
from backend.app.models.response.thesis_model import ThesisResponseModel
import pytest

def test_thesis_response_model():
  payload = {
    "symbol":"TCS",
    "verdict":"Buy",
    "summary":"TCS shows strong fundamentals with bullish technicals and positive sentiment",
    "signals":{
      "fundamental":"positive",
      "technical":"bullish",
      "sentiment":"positive",
      "valuation":"cheap"
    },
    "generated_at":datetime.now(timezone.utc)
  }

  obj = ThesisResponseModel(**payload)

  assert obj.symbol == "TCS"
  assert obj.verdict == "Buy"
  assert obj.signals["fundamental"] == "positive"
  assert obj.signals["technical"] == "bullish"