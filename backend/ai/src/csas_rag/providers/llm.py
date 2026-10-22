"""Structured chat provider for grounded answers."""
import json
import os
from urllib.request import Request, urlopen

from .embeddings import ProviderError


class OpenAIAnswerGenerator:
    def __init__(self, model=None):
        self.model = model or os.environ.get("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
        self.endpoint = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is required")

    def generate(self, system: str, prompt: str) -> dict:
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"},
            "temperature": 0,
        }).encode()
        request = Request(self.endpoint + "/chat/completions", data=body,
                          headers={"Authorization": "Bearer " + self.api_key,
                                   "Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=45) as response:
                payload = json.load(response)
            return json.loads(payload["choices"][0]["message"]["content"])
        except (OSError, ValueError, KeyError, IndexError) as error:
            raise ProviderError("Chat provider request failed") from error
