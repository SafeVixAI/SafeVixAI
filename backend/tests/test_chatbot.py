# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from core.config import Settings
from models.schemas import ChatRequest
from services.llm_service import LLMService


class FakeChatService:
    async def send_message(self, payload):
        return {
            'response': f'Handled: {payload.message}',
            'intent': 'test',
            'sources': ['unit:test'],
            'session_id': payload.session_id or 'generated-session',
        }


def test_chat_endpoint_returns_backend_chat_payload(app, auth_headers):
    with TestClient(app) as client:
        client.app.state.llm_service = FakeChatService()
        response = client.post(
            '/api/v1/chat/',
            json={
                'message': 'What is Section 185?',
                'session_id': 'session-123',
            },
            headers=auth_headers,
        )

    assert response.status_code == 200
    body = response.json()
    payload = body.get("data", body)
    assert payload['response'] == 'Handled: What is Section 185?'
    assert payload['intent'] == 'test'
    assert payload['sources'] == ['unit:test']
    assert payload['session_id'] == 'session-123'


class SlowChatbotClient:
    async def post(self, *args, **kwargs):
        await asyncio.sleep(0.05)
        raise AssertionError('wait_for should time out before this returns')


@pytest.mark.asyncio
async def test_llm_service_wait_for_timeout_returns_fallback():
    service = LLMService(Settings(chatbot_request_timeout_seconds=0.01))
    await service._client.aclose()
    service._client = SlowChatbotClient()  # type: ignore[assignment]

    response = await service.send_message(
        ChatRequest(message='Need ambulance help', session_id='timeout-session')
    )

    assert response.intent == 'emergency'
    assert response.session_id == 'timeout-session'
    assert response.sources == ['fallback:emergency']
