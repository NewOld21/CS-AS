"""Embedding providers. Production credentials are read only at runtime."""
import hashlib
import math
import os
import re

from .http import ProviderError, post_json


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
    def __init__(self, model: str | None = None, dimensions: int | None = None):
        self.model = (model or os.environ.get("GMS_EMBEDDING_MODEL")
                      or os.environ.get("EMBEDDING_MODEL") or "text-embedding-3-small")
        default_dimensions = 3072 if self.model == "text-embedding-3-large" else 1536
        configured_dimensions = os.environ.get("GMS_EMBEDDING_DIMENSIONS")
        self.dimensions = dimensions or (int(configured_dimensions) if configured_dimensions else default_dimensions)
        base_url = (os.environ.get("GMS_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
                    or "https://api.openai.com/v1")
        self.endpoint = base_url.rstrip("/")
        self.api_key = os.environ.get("GMS_KEY") or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ProviderError("GMS_KEY or OPENAI_API_KEY is required")

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not isinstance(text, str) or not text.strip() for text in texts):
            raise ValueError("Embedding input must contain non-empty strings")
        data = post_json(self.endpoint + "/embeddings", self.api_key, {
            "model": self.model, "input": texts, "dimensions": self.dimensions,
        }, timeout=30)
        try:
            rows = sorted(data["data"], key=lambda row: row["index"])
            vectors = [row["embedding"] for row in rows]
        except (KeyError, TypeError) as error:
            raise ProviderError("Embedding provider returned an invalid response") from error
        if len(vectors) != len(texts) or any(len(vector) != self.dimensions for vector in vectors):
            raise ProviderError("Embedding provider returned an invalid shape")
        return vectors
