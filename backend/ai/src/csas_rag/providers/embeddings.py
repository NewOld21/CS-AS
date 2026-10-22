"""Embedding providers. Production credentials are read only at runtime."""
import hashlib
import json
import math
import os
import re
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


class DeterministicTestEmbedding:
    """Dependency-free test double; deliberately rejected for production indexes."""

    model = "deterministic-token-hash-test-v1"

    def __init__(self, dimensions: int = 64):
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors = []
        for text in texts:
            vector = [0.0] * self.dimensions
            for token in re.findall(r"[\w가-힣]+", text.casefold()):
                value = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")
                vector[value % self.dimensions] += -1.0 if value & 1 else 1.0
            norm = math.sqrt(sum(x * x for x in vector)) or 1.0
            vectors.append([x / norm for x in vector])
        return vectors


class OpenAIEmbedding:
    def __init__(self, model: str = "text-embedding-3-small", dimensions: int = 1536):
        self.model = model
        self.dimensions = dimensions
        self.endpoint = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ProviderError("OPENAI_API_KEY is required")

    def embed(self, texts: list[str]) -> list[list[float]]:
        body = json.dumps({"model": self.model, "input": texts, "dimensions": self.dimensions}).encode()
        request = Request(
            self.endpoint + "/embeddings",
            data=body,
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                data = json.load(response)
        except (OSError, ValueError, KeyError) as error:
            raise ProviderError("Embedding provider request failed") from error
        rows = sorted(data["data"], key=lambda row: row["index"])
        vectors = [row["embedding"] for row in rows]
        if len(vectors) != len(texts) or any(len(vector) != self.dimensions for vector in vectors):
            raise ProviderError("Embedding provider returned an invalid shape")
        return vectors
