from abc import ABC, abstractmethod

class LLMClient(ABC):
    @abstractmethod
    def judge(self, prompt: str, schema: dict) -> dict: ...

def from_config(cfg: dict) -> "LLMClient":
    provider = cfg.get("provider", "mock")
    if provider == "mock":
        from .mock import MockLLM
        return MockLLM()
    if provider in ("openai", "azure_openai", "anthropic"):
        from .providers import ProviderLLM
        return ProviderLLM(cfg)
    raise ValueError(f"Provider LLM inconnu: {provider}")
