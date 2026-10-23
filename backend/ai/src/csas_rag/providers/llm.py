"""Structured chat provider for grounded answers."""
import os

from .http import ProviderError, post_json


class OpenAIAnswerGenerator:
    def __init__(self, model=None):
        self.model = (model or os.environ.get("GMS_CHAT_MODEL") or os.environ.get("CHAT_MODEL")
                      or os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1-mini"))
        base_url = (os.environ.get("GMS_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
                    or "https://api.openai.com/v1")
        self.endpoint = base_url.rstrip("/")
        self.api_key = os.environ.get("GMS_KEY") or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ProviderError("GMS_KEY or OPENAI_API_KEY is required")

    def generate(self, system: str, prompt: str) -> dict:
        return self._generate(system, prompt)

    def generate_bounded(self, system: str, prompt: str, timeout: float) -> dict:
        return self._generate(system, prompt, timeout, 0)

    def _generate(self, system: str, prompt: str, timeout=None, max_retries=None) -> dict:
        payload = {
            "model": self.model,
            "messages": [{"role": "developer", "content": system}, {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "max_completion_tokens": 4096,
        }
        if self.model.startswith("gpt-5"):
            payload["reasoning_effort"] = "low"
        try:
            response = post_json(self.endpoint + "/chat/completions", self.api_key, payload,
                                 timeout=timeout, max_retries=max_retries)
            import json
            return json.loads(response["choices"][0]["message"]["content"])
        except (ValueError, KeyError, IndexError, TypeError) as error:
            raise ProviderError("Chat provider request failed") from error
