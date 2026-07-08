# src/cqg/llm/providers.py
import os
import json
import re
from .base import LLMClient


def _extract_json(text: str) -> dict:
    """Extrait un objet JSON d'une reponse LLM, meme entouree de prose ou de balises code."""
    text = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(text[start:end + 1])
        raise


class ProviderLLM(LLMClient):
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.provider = cfg["provider"]
        self.model = cfg.get("model")
        self.api_key_env = cfg.get("api_key_env", "CQG_LLM_API_KEY")
        self.api_key = os.environ.get(self.api_key_env)
        self.base_url = cfg.get("base_url") or None

    def judge(self, prompt: str, schema: dict) -> dict:
        if self.api_key is None:
            raise RuntimeError(
                f"Cle API absente: definir la variable d'environnement {self.api_key_env}")
        if self.provider in ("openai", "azure_openai"):
            from openai import OpenAI, AzureOpenAI
            client = (AzureOpenAI(api_key=self.api_key, azure_endpoint=self.base_url,
                                  api_version=self.cfg.get("api_version", "2024-06-01"))
                      if self.provider == "azure_openai"
                      else OpenAI(api_key=self.api_key, base_url=self.base_url))
            resp = client.chat.completions.create(
                model=self.model, temperature=0,
                response_format={"type": "json_object"},
                messages=[{"role": "user", "content": prompt}])
            return _extract_json(resp.choices[0].message.content)
        from anthropic import Anthropic
        client = Anthropic(api_key=self.api_key, base_url=self.base_url)
        msg = client.messages.create(model=self.model, max_tokens=1024, temperature=0,
                                     messages=[{"role": "user", "content": prompt}])
        return _extract_json(msg.content[0].text)
