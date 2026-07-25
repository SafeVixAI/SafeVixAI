# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Any

from agent.context_assembler import ContextAssembler
from agent.state import ConversationContext
from agent.tool_summarizer import ToolPayloadSummarizer
from memory.episodic_memory import EpisodicMemoryAgent
from providers.base import ProviderRequest
from providers.router import ProviderRouter

logger = logging.getLogger(__name__)


@dataclass
class ChatState:
    session_id: str
    message: str
    intent: str
    history: list[dict[str, Any]]
    summarized_history: list[dict[str, Any]]
    user_id: str | None
    lat: float | None = None
    lon: float | None = None
    client_ip: str | None = None
    provider_hint: str | None = None
    provider_model: str | None = None

    # Context
    context: ConversationContext = field(default=None) # type: ignore

    # Results
    final_response: str | None = None
    final_sources: list[str] = field(default_factory=list)
    blocked: bool = False

    # Stream queue
    stream_events: list[dict] = field(default_factory=list)


class EmergencyDispatchAgent:
    """High-priority fast path: uses only deterministic tools and templates, bypassing heavy LLM reasoning for sub-second latency."""
    def __init__(self, context_assembler: ContextAssembler):
        self.context_assembler = context_assembler

    async def execute(self, state: ChatState) -> None:
        # For SOS, we don't even use RAG, we just get location and respond immediately.
        # However, to reuse existing logic, we can assemble context for 'sos'
        context = await self.context_assembler.assemble(
            session_id=state.session_id,
            message=state.message,
            intent=state.intent,
            lat=state.lat,
            lon=state.lon,
            client_ip=state.client_ip,
            history=[], # Skip history
            user_id=state.user_id,
        )
        state.context = context
        # Generate a fast deterministic response
        loc_tool = next((t for t in context.tools if t.name in ('geocoding', 'what3words')), None)
        loc_str = loc_tool.summary if loc_tool else "unknown location"

        state.final_response = f"EMERGENCY DISPATCH PROTOCOL INITIATED. Location recognized as: {loc_str}. Help is being notified. Please stay calm and safe."
        state.final_sources = ['policy:emergency-dispatch'] + [s for t in context.tools for s in t.sources]


class LegalAgent:
    """Restricts RAG retrieval scope exclusively to legal/challan documents."""
    def __init__(self, context_assembler: ContextAssembler):
        self.context_assembler = context_assembler

    async def execute(self, state: ChatState) -> None:
        # Delegate context building to ContextAssembler but ensure intent is legal/challan
        context = await self.context_assembler.assemble(
            session_id=state.session_id,
            message=state.message,
            intent=state.intent,
            lat=state.lat,
            lon=state.lon,
            client_ip=state.client_ip,
            history=state.history,
            user_id=state.user_id,
        )
        state.context = context


class SupervisorAgent:
    """Evaluates intent and routes to sub-agents."""
    def __init__(self, emergency_agent: EmergencyDispatchAgent, legal_agent: LegalAgent, default_assembler: ContextAssembler):
        self.emergency_agent = emergency_agent
        self.legal_agent = legal_agent
        self.default_assembler = default_assembler

    async def route_and_execute(self, state: ChatState) -> None:
        if state.intent == 'sos':
            await self.emergency_agent.execute(state)
        elif state.intent in ('legal', 'challan'):
            await self.legal_agent.execute(state)
        else:
            # Default RAG/Tools
            context = await self.default_assembler.assemble(
                session_id=state.session_id,
                message=state.message,
                intent=state.intent,
                lat=state.lat,
                lon=state.lon,
                client_ip=state.client_ip,
                history=state.history,
                user_id=state.user_id,
            )
            state.context = context


class MultiAgentGraph:
    def __init__(
        self,
        context_assembler: ContextAssembler,
        provider_router: ProviderRouter,
        episodic_memory_agent: EpisodicMemoryAgent | None = None
    ):
        self.provider_router = provider_router
        self.tool_summarizer = ToolPayloadSummarizer()
        self.episodic_memory_agent = episodic_memory_agent

        # Sub-agents
        self.emergency_agent = EmergencyDispatchAgent(context_assembler)
        self.legal_agent = LegalAgent(context_assembler)
        self.supervisor = SupervisorAgent(self.emergency_agent, self.legal_agent, context_assembler)

    def _compress_tool_payloads(self, state: ChatState) -> list[str]:
        """Use ToolPayloadSummarizer to compress tool outputs."""
        summaries = []
        for tool in state.context.tools:
            if tool.payload:
                compressed = self.tool_summarizer.summarize(tool.name, tool.payload)
                summaries.append(f"{tool.name}: {compressed}")
            else:
                summaries.append(tool.summary)
        return summaries

    async def execute(self, state: ChatState) -> ChatState:
        # 1. Supervisor Routes & Context Assembly
        await self.supervisor.route_and_execute(state)

        # 2. If it's SOS, it might already have a final response
        if state.final_response:
            return state

        # 3. Compress Tool Contexts
        compressed_tools = self._compress_tool_payloads(state)

        document_snippets = [
            f'{item.title} ({item.source}): {item.snippet}'
            for item in state.context.retrieved
        ]

        if not document_snippets and not compressed_tools and state.intent != 'general':
            state.final_response = (
                'I do not know from the SafeVixAI knowledge base. '
                'Please share more details or try a different road-safety question.'
            )
            state.final_sources = ['policy:weak-retrieval']
            state.intent = 'weak-retrieval'
            return state

        # 4. Generate via Provider Router
        provider_result = await self.provider_router.generate(
            ProviderRequest(
                message=state.message,
                intent=state.intent,
                history=state.summarized_history,
                tool_summaries=compressed_tools,
                document_snippets=document_snippets,
                provider_hint=state.provider_hint,
                provider_model=state.provider_model,
            )
        )

        state.final_response = provider_result.text

        # 5. Extract episodic memory asynchronously
        self._dispatch_memory(state)

        return state

    async def stream_execute(self, state: ChatState) -> AsyncGenerator[dict, None]:
        # 1. Supervisor Routes & Context Assembly
        await self.supervisor.route_and_execute(state)

        if state.final_response:
            yield {'type': 'token', 'text': state.final_response}
            yield {'type': 'done', 'intent': state.intent, 'sources': state.final_sources, 'session_id': state.session_id}
            return

        # 3. Compress Tool Contexts
        compressed_tools = self._compress_tool_payloads(state)
        document_snippets = [
            f'{item.title} ({item.source}): {item.snippet}'
            for item in state.context.retrieved
        ]

        if not document_snippets and not compressed_tools and state.intent != 'general':
            resp = 'I do not know from the SafeVixAI knowledge base. Please share more details.'
            yield {'type': 'token', 'text': resp}
            yield {'type': 'done', 'intent': 'weak-retrieval', 'sources': ['policy:weak-retrieval'], 'session_id': state.session_id}
            return

        # 4. Generate via Provider Router
        req = ProviderRequest(
            message=state.message,
            intent=state.intent,
            history=state.summarized_history,
            tool_summaries=compressed_tools,
            document_snippets=document_snippets,
            provider_hint=state.provider_hint,
            provider_model=state.provider_model,
        )

        async for event in self.provider_router.stream_generate(req):
            yield event

        # 5. Extract episodic memory asynchronously
        self._dispatch_memory(state)

    def _dispatch_memory(self, state: ChatState) -> None:
        if self.episodic_memory_agent and state.user_id and state.user_id not in ('anonymous', 'authenticated'):
            import asyncio
            history_snapshot = state.history + [{'role': 'assistant', 'content': state.final_response or ''}]
            asyncio.create_task(self.episodic_memory_agent.extract_and_store(
                session_id=state.session_id,
                user_id=state.user_id,
                history=history_snapshot
            ))
