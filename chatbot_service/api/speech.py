# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Query, Request

from services.speech_translation import IndicSeamlessService, speech_result_to_dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/speech', tags=['Speech'])
router_v1 = APIRouter(prefix='/api/v1/speech', tags=['Speech'])

# Max audio upload: 10 MB
_MAX_AUDIO_BYTES = 10 * 1024 * 1024
_ALLOWED_CONTENT_TYPES = {'audio/wav', 'audio/mpeg', 'audio/ogg', 'audio/webm', 'audio/flac'}


from limiter import limiter  # noqa: E402


def get_speech_service(request: Request) -> IndicSeamlessService:
    return request.app.state.speech_service


@router.get('/status')
@router_v1.get('/status')
@limiter.limit("30/minute")
async def speech_status(request: Request) -> dict:
    service = get_speech_service(request)
    return service.status()


@router.post('/translate')
@router_v1.post('/translate')
@limiter.limit("20/minute")
async def translate_speech(
    request: Request,
    target_language: str | None = Query(default=None),
) -> dict:
    # Validate content type
    ct = request.headers.get('content-type', '').split(';')[0].strip().lower()
    if ct and ct not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=415, detail=f'Unsupported audio format: {ct}')

    # Enforce upload size limit BEFORE reading full body
    content_length = request.headers.get('content-length')
    if content_length and int(content_length) > _MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail=f'Audio file too large (max {_MAX_AUDIO_BYTES // 1024 // 1024} MB).')

    audio_bytes = await request.body()
    if len(audio_bytes) > _MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail='Audio file too large (max 10 MB).')
    if not audio_bytes:
        raise HTTPException(status_code=400, detail='Empty audio body.')

    service = get_speech_service(request)

    # Offload heavy sync inference to thread pool so we don't block the event loop
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            lambda: service.translate_audio_bytes(audio_bytes, target_language=target_language),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception('Speech translation error: %s', exc)
        raise HTTPException(status_code=500, detail='Speech translation failed.') from exc

    payload = speech_result_to_dict(result)
    payload['content_type'] = ct
    return payload

