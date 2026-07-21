# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from uuid import uuid4

import logging
import html

from agent.context_assembler import ContextAssembler
from agent.multi_agent import MultiAgentGraph, ChatState
from agent.governance import AIGovernance
from agent.intent_detector import IntentDetector
from agent.safety_checker import SafetyChecker
from agent.state import ChatRequest, ChatResponse
from memory.redis_memory import ConversationMemoryStore
from memory.summarizer import ConversationSummarizer
from providers.base import ProviderRequest
from providers.router import ProviderRouter
from rag.vectorstore import LocalVectorStore

logger = logging.getLogger("safevixai.chatbot.engine")


def _log_intent_refinement(original: str, refined: str, message: str) -> None:
    if original != refined:
        logger.info("Intent refined: %s -> %s (msg='%s')", original, refined, message[:60])


class ChatEngine:
    def __init__(
        self,
        *,
        memory_store: ConversationMemoryStore,
        vectorstore: LocalVectorStore,
        intent_detector: IntentDetector,
        safety_checker: SafetyChecker,
        context_assembler: ContextAssembler,
        provider_router: ProviderRouter,
        redis_url: str | None = None,
        summarizer: ConversationSummarizer | None = None,
        episodic_memory_agent = None,
    ) -> None:
        self.memory_store = memory_store
        self.vectorstore = vectorstore
        self.intent_detector = intent_detector
        self.safety_checker = safety_checker
        self.context_assembler = context_assembler
        self.provider_router = provider_router
        self.summarizer = summarizer or ConversationSummarizer()
        # Phase 0.7: AI governance
        self.governance = AIGovernance(redis_url)
        self.redis_url = redis_url
        self.episodic_memory_agent = episodic_memory_agent
        self.multi_agent_graph = MultiAgentGraph(
            context_assembler=context_assembler,
            provider_router=provider_router,
            episodic_memory_agent=episodic_memory_agent
        )

    async def _load_user_providers(self, user_id: str | None) -> None:
        """Load user-configured providers from Redis into the router."""
        if not user_id:
            return
        try:
            import json as _json
            from redis.asyncio import Redis
            
            if not getattr(self, 'redis_url', None):
                logger.info("No Redis available — skipping user provider sync")
                return
                
            redis = Redis.from_url(self.redis_url, encoding='utf-8', decode_responses=True)
            raw = await redis.get(f"user_providers:{user_id}")
            if raw:
                configs = _json.loads(raw)
                self.provider_router.configure_user_providers(configs)
                logger.info("Loaded %d user providers for %s", len(configs), user_id)
            await redis.aclose()
        except Exception as exc:
            logger.warning("Failed to load user providers from Redis: %s", exc)

    async def chat(self, payload: ChatRequest) -> ChatResponse:
        session_id = payload.session_id or str(uuid4())
        await self.memory_store.append_message(session_id, 'user', payload.message)
        history = await self.memory_store.get_history(session_id, limit=12)

        await self._load_user_providers(payload.user_id)

        safety = self.safety_checker.evaluate(payload.message)
        if not safety.blocked:
            llama_safety = await self.safety_checker.check_llama_guard(payload.message, role="user")
            if llama_safety.blocked:
                safety = llama_safety

        if safety.blocked:
            await self.memory_store.append_message(session_id, 'assistant', safety.response or '')
            return ChatResponse(
                response=safety.response or 'I cannot help with that request.',
                intent='blocked',
                sources=['policy:safety'],
                session_id=session_id,
            )

        summarized_history, _ = self.summarizer.get_summary_for_history(history)
        intent = self.intent_detector.detect(payload.message)
        refined_intent = self.intent_detector.refine_intent(intent, payload.message, history)
        _log_intent_refinement(intent, refined_intent, payload.message)
        
        state = ChatState(
            session_id=session_id,
            message=payload.message,
            intent=refined_intent,
            history=history,
            summarized_history=summarized_history,
            user_id=payload.user_id,
            lat=payload.lat,
            lon=payload.lon,
            client_ip=payload.client_ip,
            provider_hint=payload.provider_hint,
            provider_model=payload.provider_model,
        )

        state = await self.multi_agent_graph.execute(state)

        # Phase 0.3 & Phase 4: Output safety check (static + Llama Guard)
        if state.final_response:  # pragma: no branch
            output_safety = self.safety_checker.check_output_safety(state.final_response)
            if not output_safety.blocked:
                llama_output_safety = await self.safety_checker.check_llama_guard(state.final_response, role="assistant")
                if llama_output_safety.blocked:
                    output_safety = llama_output_safety
                    
            if output_safety.blocked:
                await self.memory_store.append_message(
                    session_id, 'assistant', output_safety.response or '',
                    metadata={'intent': 'blocked_output', 'sources': ['policy:safety-output']},
                )
                return ChatResponse(
                    response=output_safety.response or 'I encountered an issue generating a safe response.',
                    intent='blocked_output',
                    sources=['policy:safety-output'],
                    session_id=session_id,
                )
            
            # Medical disclaimer
            state.final_response = self.safety_checker.add_medical_disclaimer_if_needed(
                payload.message, state.final_response
            )

        # AI governance evaluation
        governance_result = await self.governance.evaluate(
            response_text=state.final_response or '',
            retrieved_context=[
                {"content": item.snippet, "source": item.source, "title": item.title}
                for item in state.context.retrieved
            ] if state.context and state.context.retrieved else [],
            tool_results=[{"payload": tool.payload} for tool in state.context.tools] if state.context and state.context.tools else [],
            prompt=payload.message,
        )

        response_text = state.final_response or ''
        if governance_result.flagged:
            response_text = f"[⚠️ Low confidence] {response_text}"
        
        sources_list = []
        if state.context:  # pragma: no branch
            sources_list = [source for tool in state.context.tools for source in tool.sources] + [item.source for item in state.context.retrieved]
        
        sources = self._dedupe_sources(sources_list + governance_result.citations + state.final_sources)
        
        await self.memory_store.append_message(
            session_id,
            'assistant',
            response_text,
            metadata={
                'intent': state.intent,
                'sources': sources,
                'governance': {
                    'hallucination_score': governance_result.hallucination_score,
                    'factuality_score': governance_result.factuality_score,
                    'flagged': governance_result.flagged,
                    'prompt_version': governance_result.prompt_version,
                }
            },
        )

        return ChatResponse(
            response=response_text,
            intent=state.intent,
            sources=sources,
            session_id=session_id,
        )

    async def stream_chat(self, payload: ChatRequest):
        """Stream chat with real LLM token streaming.

        Yields event dicts for SSE serialization:
          {'type': 'token', 'text': str}
          {'type': 'done', 'intent': str, 'sources': list, 'session_id': str}
          {'type': 'error', 'message': str}
        """
        session_id = payload.session_id or str(uuid4())
        await self.memory_store.append_message(session_id, 'user', payload.message)
        history = await self.memory_store.get_history(session_id, limit=12)

        await self._load_user_providers(payload.user_id)

        safety = self.safety_checker.evaluate(payload.message)
        if safety.blocked:
            blocked_text = safety.response or 'I cannot help with that request.'
            await self.memory_store.append_message(session_id, 'assistant', blocked_text)
            yield {'type': 'token', 'text': blocked_text}
            yield {'type': 'done', 'intent': 'blocked', 'sources': ['policy:safety'], 'session_id': session_id}
            return

        summarized_history, _ = self.summarizer.get_summary_for_history(history)
        intent = self.intent_detector.detect(payload.message)
        refined_intent = self.intent_detector.refine_intent(intent, payload.message, history)
        _log_intent_refinement(intent, refined_intent, payload.message)
        
        state = ChatState(
            session_id=session_id,
            message=payload.message,
            intent=refined_intent,
            history=history,
            summarized_history=summarized_history,
            user_id=payload.user_id,
            lat=payload.lat,
            lon=payload.lon,
            client_ip=payload.client_ip,
            provider_hint=payload.provider_hint,
            provider_model=payload.provider_model,
        )

        full_text = ""
        last_intent = state.intent
        last_sources = []
        try:
            async for event in self.multi_agent_graph.stream_execute(state):
                if event['type'] == 'token':
                    escaped = html.escape(event['text'])
                    full_text += escaped
                    yield {'type': 'token', 'text': escaped}
                elif event['type'] == 'done':
                    last_intent = event.get('intent', state.intent)
                    last_sources = event.get('sources', [])
                    
                    # Phase 0.3 & Phase 4: Output safety check (static + Llama Guard)
                    output_safety = self.safety_checker.check_output_safety(full_text)
                    if not output_safety.blocked:
                        llama_output_safety = await self.safety_checker.check_llama_guard(full_text, role="assistant")
                        if llama_output_safety.blocked:  # pragma: no branch
                            output_safety = llama_output_safety  # pragma: no cover
                            
                    if output_safety.blocked:
                        safe_text = output_safety.response or 'I encountered an issue generating a safe response.'
                        yield {'type': 'token', 'text': safe_text}
                        yield {'type': 'done', 'intent': 'blocked_output', 'sources': ['policy:safety-output'], 'session_id': session_id}
                        await self.memory_store.append_message(
                            session_id, 'assistant', safe_text,
                            metadata={'intent': 'blocked_output', 'sources': ['policy:safety-output']},
                        )
                        return

                    # Phase 0.3: Medical disclaimer
                    full_text = self.safety_checker.add_medical_disclaimer_if_needed(payload.message, full_text)
                    state.final_response = full_text

                    governance_result = await self.governance.evaluate(
                        response_text=full_text,
                        retrieved_context=[
                            {"content": item.snippet, "source": item.source, "title": item.title}
                            for item in state.context.retrieved
                        ] if state.context and state.context.retrieved else [],
                        tool_results=[{"payload": tool.payload} for tool in state.context.tools] if state.context and state.context.tools else [],
                        prompt=payload.message,
                    )
                    
                    response_text = full_text
                    if governance_result.flagged:
                        response_text = f"[⚠️ Low confidence] {full_text}"

                    all_sources = self._dedupe_sources(last_sources + governance_result.citations)

                    await self.memory_store.append_message(
                        session_id, 'assistant', response_text,
                        metadata={
                            'intent': last_intent,
                            'sources': all_sources,
                            'governance': {
                                'hallucination_score': governance_result.hallucination_score,
                                'factuality_score': governance_result.factuality_score,
                                'flagged': governance_result.flagged,
                                'prompt_version': governance_result.prompt_version,
                            }
                        },
                    )
                    yield {'type': 'done', 'intent': last_intent, 'sources': all_sources, 'session_id': session_id}
                elif event['type'] == 'error':  # pragma: no branch
                    yield event
        except Exception as exc:
            logger.error(f"Stream chat error [session={session_id}]: {exc}", exc_info=True)
            yield {'type': 'error', 'message': 'An internal error occurred while processing your request.'}

    async def get_history(self, session_id: str) -> list[dict]:
        return await self.memory_store.get_history(session_id, limit=30)

    async def rebuild_index(self) -> dict[str, int | str]:
        await self.vectorstore.build_index(force=True)
        return await self.vectorstore.stats()

    async def stats(self) -> dict[str, int | str]:
        return await self.vectorstore.stats()

    @staticmethod
    def _dedupe_sources(values: list[str]) -> list[str]:
        seen: set[str] = set()
        deduped: list[str] = []
        for value in values:
            if not value or value in seen:
                continue
            seen.add(value)
            deduped.append(value)
        return deduped

    async def close(self) -> None:
        """Close governance resources."""
        await self.governance.close()
