# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import asyncio
import json

import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from core.config import get_settings
from core.limiter import limiter
from core.security import get_current_user
from models.schemas import ChatRequest, ChatResponse
from services.llm_service import LLMService

router = APIRouter(prefix='/api/v1/chat', tags=['Chat'])


def get_llm_service(request: Request) -> LLMService:
    return request.app.state.llm_service


def _get_fallback_response(request_message: str, session_id: str) -> ChatResponse:
    message = request_message.lower()
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


@router.post('/', response_model=ChatResponse)
@limiter.limit("5/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    current_user: dict = Depends(get_current_user),
) -> ChatResponse:
    session_id = payload.session_id or "generated-session"
    settings = get_settings()
    timeout = 1.0 if settings.environment == 'test' else settings.chatbot_request_timeout_seconds
    try:
        return await asyncio.wait_for(
            llm_service.send_message(payload),
            timeout=timeout,
        )
    except Exception:
        return _get_fallback_response(payload.message, session_id)


@router.post('/stream')
@limiter.limit("10/minute")
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service),
    current_user: dict = Depends(get_current_user),
):
    settings = get_settings()
    chatbot_base = settings.chatbot_service_url.replace('/api/v1', '')
    stream_url = f"{chatbot_base}/api/v1/chat/stream"

    async def _generate():
        settings_local = get_settings()
        headers = {"Content-Type": "application/json"}
        if settings_local.chatbot_internal_api_key:
            headers["X-Internal-Api-Key"] = settings_local.chatbot_internal_api_key
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                async with client.stream(
                    "POST",
                    stream_url,
                    json=payload.model_dump(),
                    headers=headers,
                ) as response:
                    async for chunk in response.aiter_bytes():
                        yield chunk
            except Exception:
                yield f"data: {json.dumps({'type': 'error', 'message': 'Chatbot service unavailable, using fallback'})}\n\n".encode()
                fallback = _get_fallback_response(payload.message, payload.session_id or "")
                yield f"data: {json.dumps({'type': 'token', 'text': fallback.response})}\n\n".encode()
                yield f"data: {json.dumps({'type': 'done', 'intent': fallback.intent, 'sources': fallback.sources})}\n\n".encode()

    return StreamingResponse(
        _generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
