from .base import LLMClient

class MockLLM(LLMClient):
    def __init__(self, default: dict | None = None, responses: dict | None = None):
        self.default = default or {"status": "not_evaluated", "score": None,
                                   "justification": "mock: non evalue", "evidence": None}
        self.responses = responses or {}

    def judge(self, prompt: str, schema: dict) -> dict:
        for key, resp in self.responses.items():
            if key in prompt:
                return resp
        return self.default
