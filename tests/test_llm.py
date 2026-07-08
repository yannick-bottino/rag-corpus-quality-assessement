import pytest
from cqg.llm.base import from_config
from cqg.llm.mock import MockLLM

def test_mock_returns_scripted():
    llm = MockLLM(default={"status": "scored", "score": 4, "justification": "ok", "evidence": "s1"})
    out = llm.judge("note le critere 2.5", {"type": "object"})
    assert out["score"] == 4

def test_factory_builds_mock():
    llm = from_config({"provider": "mock"})
    assert isinstance(llm, MockLLM)

def test_factory_unknown_provider_raises():
    with pytest.raises(ValueError):
        from_config({"provider": "nope"})

def test_factory_builds_providers():
    from cqg.llm.providers import ProviderLLM
    for p in ("openai", "azure_openai", "anthropic"):
        assert isinstance(from_config({"provider": p}), ProviderLLM)

def test_provider_missing_key_raises(monkeypatch):
    monkeypatch.delenv("CQG_LLM_API_KEY", raising=False)
    llm = from_config({"provider": "openai", "api_key_env": "CQG_LLM_API_KEY"})
    with pytest.raises(RuntimeError):
        llm.judge("x", {"type": "object"})

def test_extract_json_from_fenced_or_prose():
    from cqg.llm.providers import _extract_json
    assert _extract_json('```json\n{"a": 1}\n```')["a"] == 1
    assert _extract_json('Voici la reponse: {"b": 2} fin')["b"] == 2
