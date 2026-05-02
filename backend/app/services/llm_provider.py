from pathlib import Path
from threading import Lock
from typing import Any, Protocol
import requests

from app.core.config import settings

try:
  from llama_cpp import Llama
except Exception:
  Llama = None

class LLMProvider(Protocol):
  def generate(self,prompt:str)->str:
    """Generates a response based on the given prompt."""
    ...


class StubLLMProvider:
  def generate(self,prompt:str)->str:
    return "Hold Mixed Signals with balanced risk and reward"


class GeminiProvider:
  """Provider for Google Gemini API."""
  def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
    self.api_key = api_key
    self.model = model
    self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

  def generate(self, prompt: str) -> str:
    """Call Gemini REST API to generate thesis."""
    try:
      url = f"{self.base_url}/{self.model}:generateContent"
      headers = {"Content-Type": "application/json"}
      payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
          "temperature": 0.3,
          "maxOutputTokens": 256,
        }
      }
      params = {"key": self.api_key}
      response = requests.post(url, json=payload, headers=headers, params=params, timeout=10)
      response.raise_for_status()
      result = response.json()
      if "candidates" in result and len(result["candidates"]) > 0:
        candidate = result["candidates"][0]
        if "content" in candidate and "parts" in candidate["content"] and len(candidate["content"]["parts"]) > 0:
          return candidate["content"]["parts"][0].get("text", "Hold Mixed Signals")
      return "Hold Mixed Signals"
    except Exception as e:
      print(f"Gemini API error: {e}")
      return "Hold Mixed Signals"


class LlamaCppLoraProvider:
  def __init__(
    self,
    model_path: str,
    lora_path: str,
    max_tokens: int = 120,
    temperature: float = 0.2,
  ) -> None:
    if Llama is None:
      raise RuntimeError("llama_cpp is not installed. Install llama-cpp-python to use local LLM provider.")

    self.max_tokens = max_tokens
    self.temperature = temperature
    self._lock = Lock()

    resolved_model_path = str(Path(model_path).resolve())
    resolved_lora_path = str(Path(lora_path).resolve())

    self._llm = Llama(
      model_path=resolved_model_path,
      lora_path=resolved_lora_path,
    )

  def generate(self,prompt:str)->str:
    with self._lock:
      output: dict[str, Any] = self._llm(
        prompt,
        max_tokens=self.max_tokens,
        temperature=self.temperature,
      )
    return str(output["choices"][0]["text"]).strip()


_LOCAL_PROVIDER: LlamaCppLoraProvider | None = None


def get_local_llm_provider() -> LlamaCppLoraProvider:
  global _LOCAL_PROVIDER
  if _LOCAL_PROVIDER is None:
    _LOCAL_PROVIDER = LlamaCppLoraProvider(
      model_path=settings.LLM_MODEL_PATH,
      lora_path=settings.LLM_LORA_PATH,
      max_tokens=settings.LLM_MAX_TOKENS,
      temperature=settings.LLM_TEMPERATURE,
    )
  return _LOCAL_PROVIDER