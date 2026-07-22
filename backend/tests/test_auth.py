# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

import core.security as security_module
from api.v1.user import get_user_profile

ALGORITHM = security_module.ALGORITHM
create_access_token = security_module.create_access_token


def test_verify_rejects_missing_token(app):
    with TestClient(app) as client:
        response = client.get('/api/v1/auth/verify')

    assert response.status_code == 401


def test_verify_rejects_static_mock_token(app):
    with TestClient(app) as client:
        response = client.get(
            '/api/v1/auth/verify',
            headers={'Authorization': 'Bearer mock-jwt-token-for-hackathon'},
        )

    assert response.status_code == 401


def test_verify_accepts_operator_jwt(app):
    token = create_access_token({'sub': 'operator@example.com', 'role': 'operator'})

    with TestClient(app) as client:
        response = client.get(
            '/api/v1/auth/verify',
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == 200
    assert response.json()['data']['sub'] == 'operator@example.com'


def test_verify_accepts_supabase_auth_jwt(app, monkeypatch):
    import secrets
    secret = secrets.token_hex(32)
    monkeypatch.setattr(security_module, 'SUPABASE_JWT_SECRET', secret)
    monkeypatch.setattr(security_module, 'SUPABASE_JWT_AUDIENCE', 'authenticated')
    token = jwt.encode(
        {
            'sub': 'supabase-user-id',
            'aud': 'authenticated',
            'role': 'authenticated',
            'email': 'user@example.com',
            'exp': datetime.now(UTC) + timedelta(minutes=10),
        },
        secret,
        algorithm=ALGORITHM,
    )

    with TestClient(app) as client:
        response = client.get(
            '/api/v1/auth/verify',
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == 200
    assert response.json()['data']['sub'] == 'supabase-user-id'


def test_profile_endpoint_requires_auth(app):
    with TestClient(app) as client:
        response = client.get(f'/api/v1/users/{uuid.uuid4()}')

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_profile_owner_mismatch_returns_not_found():
    from starlette.datastructures import Headers
    from starlette.requests import Request

    class EmptyResult:
        def scalar_one_or_none(self):
            return None

    class FakeSession:
        async def execute(self, _query):
            return EmptyResult()

    mock_request = Request(scope={
        "type": "http",
        "method": "GET",
        "headers": Headers().raw,
        "path": "/api/v1/users/",
    })

    with pytest.raises(HTTPException) as exc:
        await get_user_profile(
            request=mock_request,
            user_id=uuid.uuid4(),
            db=FakeSession(),  # type: ignore[arg-type]
            current_user={'sub': 'caller-user-id'},
        )

    assert exc.value.status_code == 404


def test_verify_rejects_invalid_role_claim(app):
    # 'super-admin' is not a valid Role enum member
    token = create_access_token({'sub': 'attacker@example.com'}, role='super-admin')

    with TestClient(app) as client:
        response = client.get(
            '/api/v1/auth/verify',
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == 401
    assert "Invalid role claim in token" in response.json()['detail']


def test_require_role_decorator_insufficient_permissions(app):
    # A user with role='user' tries to access a circuit breaker endpoint requiring Role.ADMIN (or Role.OPERATOR/ADMIN in other contexts)
    # Let's hit '/api/v1/circuit-breaker/some-breaker' which requires Role.ADMIN
    token = create_access_token({'sub': 'user@example.com'}, role='user')

    with TestClient(app) as client:
        response = client.get(
            '/api/v1/circuit-breaker/some-breaker',
            headers={'Authorization': f'Bearer {token}'},
        )

    assert response.status_code == 403
    assert "Insufficient permissions" in response.json()['detail']

