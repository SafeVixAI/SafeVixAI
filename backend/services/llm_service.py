# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import logging
from uuid import uuid4

import httpx
from pydantic import ValidationError

from core.config import Settings
from models.schemas import ChatRequest, ChatResponse

logger = logging.getLogger("safevixai.llm_service")


class LLMService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        headers = {
            'Accept': 'application/json',
            'User-Agent': settings.http_user_agent,
        }
        if settings.chatbot_internal_api_key:
            headers['X-Internal-Api-Key'] = settings.chatbot_internal_api_key
        self._client = httpx.AsyncClient(
            base_url=settings.chatbot_service_url,
            timeout=settings.chatbot_request_timeout_seconds,
            headers=headers,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def send_message(self, request: ChatRequest) -> ChatResponse:
        payload = request.model_dump(exclude_none=True)
        session_id = request.session_id or str(uuid4())
        try:
            response = await asyncio.wait_for(
                self._client.post('/chat/', json=payload),
                timeout=self.settings.chatbot_request_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            return ChatResponse.model_validate(data)
        except TimeoutError:
            logger.warning(
                "Chatbot service timed out after %.1fs for session %s",
                self.settings.chatbot_request_timeout_seconds,
                session_id,
                extra={"service": "llm"},
            )
            return self._fallback_response(request, session_id=session_id)
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Chatbot service returned HTTP %s for session %s",
                exc.response.status_code,
                session_id,
                extra={"service": "llm"},
            )
            return self._fallback_response(request, session_id=session_id)
        except httpx.RequestError:
            logger.exception("Chatbot service request failed for session %s", session_id, extra={"service": "llm"})
            return self._fallback_response(request, session_id=session_id)
        except (ValidationError, json.JSONDecodeError):
            logger.exception("Chatbot response validation failed for session %s", session_id, extra={"service": "llm"})
            return self._fallback_response(request, session_id=session_id)

    def _fallback_response(self, request: ChatRequest, *, session_id: str) -> ChatResponse:
        message = request.message.lower()
        if any(term in message for term in ('ambulance', 'hospital', 'accident', 'sos', 'emergency')):
            response = (
                'The live chatbot service is unavailable right now, so I am switching to a safe fallback. '
                'If this is urgent, call 112 immediately. You can also use the emergency locator to find '
                'nearby hospitals, police, or ambulances from the main app.'
            )
            intent = 'emergency'
            sources = ['fallback:emergency']
        elif any(term in message for term in ('fine', 'challan', 'section 185', 'helmet', 'seatbelt')):
            response = (
                'The live legal assistant is temporarily offline. You can still use the challan calculator '
                'endpoint for deterministic fine estimates while the chatbot service reconnects.'
            )
            intent = 'challan'
            sources = ['fallback:challan']
        else:
            response = (
                'The live chatbot service is warming up. Please try again in a moment, or use the dedicated '
                'emergency, challan, and road issue tools in the meantime.'
            )
            intent = 'fallback'
            sources = ['fallback:service']

        return ChatResponse(
            response=response,
            intent=intent,
            sources=sources,
            session_id=session_id,
        )
