from datetime import datetime,timezone
from backend.app.models.response.thesis_model import ThesisResponseModel
import pytest
from pydantic import ValidationError

def test_thesis_valid_response_model():
  """Test that thesis response model validates correctly with proper signal labels."""
  payload = {
    "symbol":"TCS",
    "verdict":"Hold",
    "summary":"TCS shows neutral fundamentals and sentiment with fair valuation",
    "signals":{
      "fundamental":"neutral",
      "technical":"neutral",
      "sentiment":"neutral",
      "valuation":"fair"
    },
    "generated_at":datetime.now(timezone.utc)
  }
  # This should now pass validation (no exception)
  obj = ThesisResponseModel(**payload)
  assert obj.symbol == "TCS"
  assert obj.verdict == "Hold"