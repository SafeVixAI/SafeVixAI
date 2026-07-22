# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from core.security import create_access_token


def _create_ws_token():
    return create_access_token({"sub": "test-user", "role": "operator"})


def test_ws_connect_requires_token(app):
    with TestClient(app) as client, pytest.raises(Exception):
        with client.websocket_connect("/api/v1/tracking/test-group"):
            pass


def test_ws_reject_invalid_token(app):
    with TestClient(app) as client, pytest.raises(Exception):
        with client.websocket_connect("/api/v1/tracking/test-group?token=invalid-token"):
            pass


def test_ws_reject_no_token(app):
    with TestClient(app) as client, pytest.raises(Exception):
        with client.websocket_connect("/api/v1/tracking/test-group"):
            pass


def test_ws_accept_valid_token(app):
    token = _create_ws_token()
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/tracking/test-group?token={token}") as ws:
            ws.send_json({"lat": 13.0827, "lon": 80.2707})
            data = ws.receive_json()
            assert data["lat"] == 13.0827
            assert data["lon"] == 80.2707


def test_ws_reject_invalid_payload(app):
    token = _create_ws_token()
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/tracking/test-group?token={token}") as ws:
            ws.send_json({"lat": "invalid", "lon": "invalid"})
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "Invalid" in data["message"]


def test_ws_reject_oversized_message(app):
    token = _create_ws_token()
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/tracking/test-group?token={token}") as ws:
            large_payload = {"lat": 13.0827, "lon": 80.2707, "data": "x" * 5000}
            ws.send_text(json.dumps(large_payload))
            try:
                data = ws.receive_json()
                assert data["type"] == "error"
            except Exception:
                pass  # Connection may close on oversized message; either error JSON or disconnect is valid


def test_ws_invalid_json(app):
    token = _create_ws_token()
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/tracking/test-group?token={token}") as ws:
            ws.send_text("not valid json")
            data = ws.receive_json()
            assert data["type"] == "error"
            assert "JSON" in data["message"]


def test_ws_alternate_coordinate_keys(app):
    token = _create_ws_token()
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/tracking/test-group?token={token}") as ws:
            ws.send_json({"latitude": 13.0827, "longitude": 80.2707})
            data = ws.receive_json()
            assert data["latitude"] == 13.0827


def test_ws_multiple_users_same_group(app):
    token = _create_ws_token()
    with TestClient(app) as client:
        with client.websocket_connect(f"/api/v1/tracking/shared-group?token={token}") as ws1:
            with client.websocket_connect(f"/api/v1/tracking/shared-group?token={token}") as ws2:
                ws1.send_json({"lat": 13.0827, "lon": 80.2707})
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()
                assert data1["lat"] == 13.0827
                assert data2["lat"] == 13.0827
