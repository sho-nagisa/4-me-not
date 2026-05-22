from __future__ import annotations

from collections import Counter
import hashlib
import logging
import os
import re

import httpx

from backend.services.search.utils import normalize_text, normalize_vector


logger = logging.getLogger(__name__)


class SearchEmbeddingProvider:
    fallback_model = "local-hash-v1"

    def __init__(self) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.openai_model = os.environ.get(
            "OPENAI_EMBEDDING_MODEL",
            "text-embedding-3-small",
        )
        self.dimension = int(os.environ.get("SEARCH_FALLBACK_EMBEDDING_DIM", "384"))

    @property
    def preferred_model(self) -> str:
        return self.openai_model if self.api_key else self.fallback_model

    def embed(self, text: str) -> tuple[list[float], str]:
        if self.api_key:
            try:
                return self._embed_with_openai(text), self.openai_model
            except Exception:
                logger.exception("OpenAI embedding failed; using local fallback")

        return self._embed_locally(text), self.fallback_model

    def _embed_with_openai(self, text: str) -> list[float]:
        response = httpx.post(
            "https://api.openai.com/v1/embeddings",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.openai_model,
                "input": text[:12000],
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        embedding = payload["data"][0]["embedding"]
        return [float(value) for value in embedding]

    def _embed_locally(self, text: str) -> list[float]:
        normalized = normalize_text(text)
        features: Counter[str] = Counter()

        for token in re.findall(r"[\w]+", normalized):
            if len(token) > 1:
                features[token] += 2

        compact = re.sub(r"\s+", "", normalized)
        for width, weight in ((2, 1), (3, 2), (4, 1)):
            if len(compact) < width:
                continue
            for index in range(len(compact) - width + 1):
                features[compact[index : index + width]] += weight

        vector = [0.0] * self.dimension
        for feature, weight in features.items():
            digest = hashlib.sha256(feature.encode("utf-8")).digest()
            bucket = int.from_bytes(digest[:4], "big") % self.dimension
            vector[bucket] += float(weight)

        return normalize_vector(vector)


