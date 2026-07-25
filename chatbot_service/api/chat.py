# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import html
import json
import logging
import uuid

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Request  # noqa: E402
from fastapi.responses import StreamingResponse  # noqa: E402

from agent.graph import ChatEngine  # noqa: E402
from agent.state import ChatRequest, ChatResponse  # noqa: E402
from config import get_settings  # noqa: E402

router = APIRouter(prefix='/api/v1/chat', tags=['Chat'])


from limiter import limiter  # noqa: E402


def get_engine(request: Request) -> ChatEngine:
    return request.app.state.chat_engine


def verify_internal_auth(
    request: Request,
    x_internal_api_key: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    if settings.environment == 'production' and not settings.internal_api_key:
        raise HTTPException(
            status_code=500,
            detail="CHATBOT_INTERNAL_API_KEY not configured. Chat endpoints require auth in production."
        )
    if settings.internal_api_key:
        import hmac
        if not x_internal_api_key or not hmac.compare_digest(x_internal_api_key, settings.internal_api_key):
            raise HTTPException(status_code=403, detail="Invalid internal API key")


@router.post('/', response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    engine: ChatEngine = Depends(get_engine),
    _auth: None = Depends(verify_internal_auth),
) -> ChatResponse:
    """Standard blocking chat — returns full response at once."""
    if not payload.client_ip:  # pragma: no branch
        forwarded = request.headers.get('x-forwarded-for', '')
        payload.client_ip = forwarded.split(',')[0].strip() or (request.client.host if request.client else None)
    try:
        result = await asyncio.wait_for(engine.chat(payload), timeout=60.0)
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Chat request timed out. Please try again.")
    result.response = html.escape(result.response)
    return result


@router.post('/stream')
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    engine: ChatEngine = Depends(get_engine),
    _auth: None = Depends(verify_internal_auth),
) -> StreamingResponse:
    """SSE streaming chat — sends tokens as they arrive from the LLM.

    Client should consume text/event-stream and parse JSON events:
      data: {"type": "token", "text": "..."}\n\n
      data: {"type": "done", "intent": "...", "sources": [...], "session_id": "..."}\n\n
      data: {"type": "error", "message": "..."}\n\n

    Uses true LLM token streaming (not simulated word-split).
    """
    async def event_generator():
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        try:
            if not payload.client_ip and request.client:  # pragma: no branch
                payload.client_ip = request.client.host

            stream_timeout = get_settings().http_timeout_seconds + 15.0
            async with asyncio.timeout(stream_timeout):
                async for event in engine.stream_chat(payload):
                    event['request_id'] = request_id
                    if event['type'] in ('token',):
                        event['text'] = html.escape(event.get('text', ''))
                        yield f'data: {json.dumps(event)}\n\n'
                    elif event['type'] == 'done' or event['type'] == 'error':
                        yield f'data: {json.dumps(event)}\n\n'
                        return

        except TimeoutError:
            err_data = json.dumps({'type': 'error', 'message': 'Stream timed out. Please try again.', 'request_id': request_id})
            yield f'data: {err_data}\n\n'
            return
        except Exception as exc:
            logger.exception("Chat stream error [request_id=%s]: %s", request_id, exc)
            err_data = json.dumps({'type': 'error', 'message': 'An internal error occurred while processing your request.', 'request_id': request_id})
            yield f'data: {err_data}\n\n'

    return StreamingResponse(
        event_generator(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        },
    )


@router.get('/history/{session_id}')
async def get_history(
    request: Request,
    session_id: str = Path(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$"),
    x_admin_secret: str | None = Header(default=None),
    engine: ChatEngine = Depends(get_engine),
) -> dict:
    settings = get_settings()
    import hmac
    if not settings.admin_secret or not hmac.compare_digest(x_admin_secret or '', settings.admin_secret):
        raise HTTPException(status_code=403, detail='Chat history access requires admin authorization')
    return {'session_id': session_id, 'messages': await engine.get_history(session_id)}


@router.get('/health')
async def health(request: Request) -> dict:
    return {'status': 'ok', 'service': 'safevixai-chatbot'}
