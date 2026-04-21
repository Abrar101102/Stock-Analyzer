from pathlib import Path
from threading import Lock
from typing import Any, Protocol

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