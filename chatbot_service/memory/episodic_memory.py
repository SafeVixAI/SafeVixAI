# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import logging
from pathlib import Path

from providers.router import ProviderRouter
from providers.base import ProviderRequest
from rag.vectorstore import LocalVectorStore, DocumentChunk

logger = logging.getLogger(__name__)

class EpisodicMemoryAgent:
    """Agent responsible for compressing short-term session history into long-term semantic vectors."""

    def __init__(self, router: ProviderRouter, database_url: str, persist_dir: Path):
        self.router = router
        self.vectorstore = LocalVectorStore(
            database_url=database_url,
            data_dir=persist_dir / "user_memory_data",
            collection_name='user_memory'
        )

    async def extract_and_store(self, session_id: str, user_id: str, history: list[dict]):
        """Analyze a conversation history, extract key facts, and store in the user's episodic memory."""
        if not history or len(history) < 2:
            return

        # Prepare prompt for extraction (load from versioned YAML if available)
        history_text = "\n".join([f"{msg.get('role')}: {msg.get('content')}" for msg in history])
        try:
            from prompts import get_episodic_memory_prompt
            prompt = get_episodic_memory_prompt(history_text)
        except ImportError:
            prompt = (
                "You are a memory extraction agent. Read the following conversation history and extract key "
                "user preferences, context, or facts that should be remembered for future sessions "
                "(e.g., user's location, vehicle type, medical condition, frequent problems). "
                "Output ONLY a concise bulleted list of facts. If there is nothing worth remembering, output exactly 'NO_FACTS'.\n\n"
                f"Conversation History:\n{history_text}"
            )

        request = ProviderRequest(
            message=prompt,
            intent="general",
            history=[]
        )

        try:
            result = await self.router.generate(request)
            facts = result.text.strip()
            
            if facts and facts != "NO_FACTS" and "NO_FACTS" not in facts:
                # Store in vector database
                import uuid
                chunk_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    source=f"session_{session_id}",
                    title=f"User {user_id} Memory",
                    category=user_id,
                    content=facts
                )
                
                await self.vectorstore._upsert_pg([chunk])
                logger.info("Stored episodic memory for user %s from session %s", user_id, session_id)

        except Exception as e:
            logger.error("Failed to extract episodic memory: %s", e)

    async def retrieve_memory(self, user_id: str, query: str, top_k: int = 3) -> list[str]:
        """Retrieve relevant memories for a user given a query."""
        results = await self.vectorstore.search(query, top_k=top_k, scopes={user_id})
        return [chunk.content for chunk, score in results]
