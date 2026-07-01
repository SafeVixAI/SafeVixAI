# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from rag.retriever import RetrievalResult, Retriever


class LegalSearchTool:
    def __init__(self, retriever: Retriever) -> None:
        self.retriever = retriever

    async def search(self, query: str, *, top_k: int = 4) -> list[RetrievalResult]:
        return await self.retriever.retrieve(query, top_k=top_k, scopes={'legal'})
