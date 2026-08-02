# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import hashlib
import math
import re
from typing import Any

TOKEN_PATTERN = re.compile(r'[a-zA-Z][a-zA-Z0-9_]{1,}')


def normalize_text(value: str) -> str:
    return re.sub(r'\s+', ' ', value).strip()


def tokenize(value: str) -> set[str]:
    return {match.group(0).lower() for match in TOKEN_PATTERN.finditer(value)}


def score_query(query: str, text: str) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    text_tokens = tokenize(text)
    if not text_tokens:
        return 0.0
    overlap = len(query_tokens & text_tokens)
    phrase_bonus = 0.0
    lowered_query = normalize_text(query).lower()
    lowered_text = normalize_text(text).lower()
    if lowered_query and lowered_query in lowered_text:
        phrase_bonus = 1.5
    return overlap + phrase_bonus + min(len(lowered_text), 1200) / 5000


def hash_embedding(value: str, *, dimensions: int = 384) -> list[float]:
    """Deterministic local embedding used for both Chroma ingestion and retrieval."""
    vector = [0.0] * dimensions
    for token in tokenize(value):
        index = int(hashlib.sha256(token.encode('utf-8')).hexdigest()[:8], 16) % dimensions
        vector[index] += 1.0
    norm = math.sqrt(sum(item * item for item in vector))
    if norm == 0:
        return vector
    return [item / norm for item in vector]


class LocalHashEmbeddingFunction:
    def __init__(self, dimensions: int = 384) -> None:
        self.dimensions = dimensions

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [hash_embedding(item, dimensions=self.dimensions) for item in input]

    @staticmethod
    def name() -> str:
        return 'safevixai-local-hash'

    @staticmethod
    def build_from_config(config: dict[str, int]) -> LocalHashEmbeddingFunction:
        return LocalHashEmbeddingFunction(dimensions=int(config.get('dimensions', 384)))

    def get_config(self) -> dict[str, int]:
        return {'dimensions': self.dimensions}

    def default_space(self) -> str:
        return 'cosine'

    def supported_spaces(self) -> list[str]:
        return ['cosine']

    def is_legacy(self) -> bool:
        return False


class SentenceTransformerEmbeddingFunction:
    """Chroma embedding function backed by a real sentence-transformers model."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name
        self._model: Any | None = None
        self._fallback = LocalHashEmbeddingFunction()

    def _load_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer

                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                return None
        return self._model

    def __call__(self, input: list[str]) -> list[list[float]]:
        model = self._load_model()
        if model is None:
            return self._fallback(input)
        encoded = model.encode(
            input,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return encoded.tolist()

    @staticmethod
    def name() -> str:
        return 'safevixai-sentence-transformer'

    @staticmethod
    def build_from_config(config: dict[str, str]) -> SentenceTransformerEmbeddingFunction:
        return SentenceTransformerEmbeddingFunction(
            model_name=config.get('model_name', 'sentence-transformers/all-MiniLM-L6-v2')
        )

    def get_config(self) -> dict[str, str]:
        return {'model_name': self.model_name}

    def default_space(self) -> str:
        return 'cosine'

    def supported_spaces(self) -> list[str]:
        return ['cosine']

    def is_legacy(self) -> bool:
        return False


def build_embedding_function(model_name: str | None = None):
    if not model_name or not isinstance(model_name, str):
        normalized = 'sentence-transformers/all-MiniLM-L6-v2'
    else:
        normalized = model_name.strip() or 'sentence-transformers/all-MiniLM-L6-v2'
    if normalized in {'safevixai-local-hash', 'local-hash', 'hash'}:
        return LocalHashEmbeddingFunction()
    return SentenceTransformerEmbeddingFunction(normalized)
