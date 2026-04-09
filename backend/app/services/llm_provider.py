from typing import Protocol

class LLMProvider(Protocol):
  def generate(self,prompt:str)->str:
    """Generates a response based on the given prompt."""
    ...


class StubLLMProvider:
  def generate(self,prompt:str)->str:
    return "Hold Mixed Signals with balanced risk and reward"