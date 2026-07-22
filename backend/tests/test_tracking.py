# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.v1.tracking import _is_valid_location, _is_valid_tracking_payload, router
from core.security import create_access_token

app = FastAPI()
app.include_router(router)
client = TestClient(app)

def test_is_valid_location():
    assert _is_valid_location(10.0, minimum=-90, maximum=90) is True
    assert _is_valid_location(100.0, minimum=-90, maximum=90) is False
    assert _is_valid_location(None, minimum=-90, maximum=90) is True
    assert _is_valid_location("invalid", minimum=-90, maximum=90) is False

def test_is_valid_tracking_payload():
    assert _is_valid_tracking_payload({"lat": 10.0, "lon": 20.0}) is True
    assert _is_valid_tracking_payload({"latitude": 10.0, "longitude": 20.0}) is True
    assert _is_valid_tracking_payload({"lat": 100.0, "lon": 20.0}) is False
    assert _is_valid_tracking_payload({"lat": 10.0, "lon": 200.0}) is False
    assert _is_valid_tracking_payload("invalid") is False

def test_websocket_missing_token():
    from starlette.websockets import WebSocketDisconnect
    try:
        with client.websocket_connect("/api/v1/tracking/test-group", headers={"origin": "http://localhost:3000"}):
            pass
    except WebSocketDisconnect as e:
        assert e.code == 1008

def test_websocket_invalid_payload(monkeypatch):
    monkeypatch.setattr("api.v1.tracking._origin_allowed", lambda x: True)
    # Generate a valid token
    token = create_access_token({"sub": "testuser"})

    with client.websocket_connect(f"/api/v1/tracking/test-group?token={token}") as websocket:
        # Send invalid JSON
        websocket.send_text("invalid json")
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert response["message"] == "Invalid JSON"

        # Send invalid payload
        websocket.send_json({"lat": 100.0, "lon": 20.0})
        response = websocket.receive_json()
        assert response["type"] == "error"
        assert response["message"] == "Invalid tracking payload"

def test_websocket_valid_payload(monkeypatch):
    monkeypatch.setattr("api.v1.tracking._origin_allowed", lambda x: True)
    token = create_access_token({"sub": "testuser"})

    with client.websocket_connect(f"/api/v1/tracking/test-group?token={token}") as websocket:
        payload = {"lat": 10.0, "lon": 20.0}
        websocket.send_json(payload)
        # Should broadcast back to us
        response = websocket.receive_json()
        assert response == payload
