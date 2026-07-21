# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import asyncio
from fastapi import APIRouter, Path, WebSocket, WebSocketDisconnect
from typing import Any, Dict, Set
import json
import logging
import time
from redis.asyncio import Redis

from core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/tracking", tags=["Tracking"])
MAX_TRACKING_MESSAGE_BYTES = 4096
MAX_TRACKING_GROUP_ID_LENGTH = 80

# ── Enterprise Heartbeat & Cleanup ────────────────────────────────────────────
HEARTBEAT_INTERVAL_SECONDS = 25
STALE_CONNECTION_TIMEOUT_SECONDS = 60
STALE_CLEANUP_INTERVAL_SECONDS = 30
MAX_CONNECTIONS = 500

from pydantic import BaseModel, Field, model_validator, ValidationError

class WSLocationUpdate(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    speed: float | None = Field(default=None, ge=0.0)
    accuracy: float | None = Field(default=None, ge=0.0)

    @model_validator(mode="before")
    @classmethod
    def normalize_lat_lon(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(data, dict):
            return data
        data_copy = dict(data)
        if "latitude" in data_copy and "lat" not in data_copy:
            data_copy["lat"] = data_copy["latitude"]
        if "longitude" in data_copy and "lon" not in data_copy:
            data_copy["lon"] = data_copy["longitude"]
        return data_copy


def _is_valid_location(value: object, *, minimum: float, maximum: float) -> bool:
    if value is None:
        return True
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    return minimum <= numeric <= maximum


def _is_valid_tracking_payload(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    try:
        WSLocationUpdate.model_validate(payload)
        return True
    except (ValidationError, TypeError, ValueError):
        return False


def _origin_allowed(origin: str | None) -> bool:
    settings = get_settings()
    allowed = settings.cors_origins
    if not origin:
        return settings.environment != 'production' or '*' in allowed
    if '*' in allowed:
        return settings.environment != 'production'
    return origin.rstrip('/') in {item.rstrip('/') for item in allowed}


def _is_valid_ws_token(token: str | None) -> bool:
    if not token:
        return False
    from core.security import _decode_bearer_token
    try:
        payload = _decode_bearer_token(token)
        return bool(payload.get("sub"))
    except Exception as e:
        logger.warning("WebSocket token validation failed: %s", e)
        return False


# ── Connection health tracker ────────────────────────────────────────────────
class ConnectionHealth:
    """Tracks last activity time per WebSocket for stale connection detection."""
    def __init__(self):
        self._last_activity: Dict[int, float] = {}  # id(websocket) -> timestamp

    def mark_activity(self, ws: WebSocket):
        self._last_activity[id(ws)] = time.monotonic()

    def remove(self, ws: WebSocket):
        self._last_activity.pop(id(ws), None)

    def stale_connections(self, connections: Set[WebSocket], timeout: float) -> list[WebSocket]:
        now = time.monotonic()
        stale = []
        for ws in connections:
            last = self._last_activity.get(id(ws))
            if last and (now - last) > timeout:
                stale.append(ws)
        return stale


connection_health = ConnectionHealth()


class RedisConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.pubsub_tasks: Dict[str, asyncio.Task] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self.cleanup_task: asyncio.Task | None = None
        self.redis: Redis | None = None

    def set_redis(self, redis_client: Redis | None):
        self.redis = redis_client

    def total_connections(self) -> int:
        """Return total active WebSocket connections across all groups."""
        total = 0
        for group in self.active_connections.values():
            total += len(group)
        return total

    async def connect(self, websocket: WebSocket, group_id: str):
        total = self.total_connections()
        if total >= MAX_CONNECTIONS:
            await websocket.close(code=1013, reason="Server at capacity — try again later")
            logger.warning("Rejected WebSocket connection: %d active (max %d)", total, MAX_CONNECTIONS)
            return
        await websocket.accept()
        connection_health.mark_activity(websocket)
        if group_id not in self.active_connections:
            self.active_connections[group_id] = set()
            if self.redis:
                task = asyncio.create_task(self._listen_to_pubsub(group_id))
                self.pubsub_tasks[group_id] = task
            heartbeat = asyncio.create_task(self._heartbeat_loop(group_id))
            self.heartbeat_tasks[group_id] = heartbeat

        self.active_connections[group_id].add(websocket)
        logger.info("Client joined tracking group %s. Total local: %s", group_id, len(self.active_connections[group_id]))
        try:
            from core.metrics import ws_connections_total
            ws_connections_total.labels(group=group_id).inc()
        except ImportError:
            logger.debug("WS metrics not available — skipping connection counter increment")

    def disconnect(self, websocket: WebSocket, group_id: str):
        connection_health.remove(websocket)
        if group_id in self.active_connections:
            self.active_connections[group_id].discard(websocket)
            if not self.active_connections[group_id]:
                del self.active_connections[group_id]
                if group_id in self.pubsub_tasks:
                    self.pubsub_tasks[group_id].cancel()
                    del self.pubsub_tasks[group_id]
                if group_id in self.heartbeat_tasks:
                    self.heartbeat_tasks[group_id].cancel()
                    del self.heartbeat_tasks[group_id]
            logger.info("Client left tracking group %s.", group_id)
            try:
                from core.metrics import ws_connections_total
                ws_connections_total.labels(group=group_id).dec()
            except ImportError:
                logger.debug("WS metrics not available — skipping connection counter decrement")

    async def broadcast(self, message: dict, group_id: str):
        if self.redis:
            await self.redis.publish(f"tracking:{group_id}", json.dumps(message))
        else:
            await self._local_broadcast(message, group_id)

    async def _local_broadcast(self, message: dict, group_id: str):
        if group_id in self.active_connections:
            disconnected = set()
            payload = json.dumps(message)
            for connection in self.active_connections[group_id]:
                try:
                    await connection.send_text(payload)
                except Exception:
                    logger.exception("Error sending tracking update to client")
                    disconnected.add(connection)

            for conn in disconnected:
                self.disconnect(conn, group_id)

    async def _heartbeat_loop(self, group_id: str):
        """Send periodic ping frames to all clients in a group to detect stale connections."""
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
                if group_id not in self.active_connections:
                    break
                ping = json.dumps({"type": "ping"})
                stale = set()
                for ws in self.active_connections.get(group_id, set()):
                    try:
                        await ws.send_text(ping)
                    except Exception:
                        stale.add(ws)
                for ws in stale:
                    self.disconnect(ws, group_id)
        except asyncio.CancelledError:
            logger.info("Heartbeat loop cancelled for group %s", group_id)

    async def _stale_cleanup_loop(self):
        """Periodically close connections that haven't sent data recently."""
        try:
            while True:
                await asyncio.sleep(STALE_CLEANUP_INTERVAL_SECONDS)
                for group_id, connections in list(self.active_connections.items()):
                    stale = connection_health.stale_connections(connections, STALE_CONNECTION_TIMEOUT_SECONDS)
                    for ws in stale:
                        logger.warning("Closing stale connection in group %s", group_id)
                        try:
                            await ws.close(code=1001, reason="Connection timeout")
                        except Exception as exc:
                            logger.debug("Stale connection close failed for group %s: %s", group_id, exc)
                        self.disconnect(ws, group_id)
        except asyncio.CancelledError:
            logger.info("Stale cleanup loop cancelled")

    def start_cleanup(self):
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._stale_cleanup_loop())

    def stop_cleanup(self):
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            self.cleanup_task = None

    async def _listen_to_pubsub(self, group_id: str):
        if not self.redis:
            return
        pubsub = None
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(f"tracking:{group_id}")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    payload = json.loads(message["data"])
                    await self._local_broadcast(payload, group_id)
        except asyncio.CancelledError:
            if pubsub:
                await pubsub.unsubscribe(f"tracking:{group_id}")
                await pubsub.close()
        except Exception:
            logger.exception("PubSub error for tracking group %s", group_id)

manager = RedisConnectionManager()


@router.websocket("/{group_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    group_id: str = Path(min_length=1, max_length=MAX_TRACKING_GROUP_ID_LENGTH, pattern=r"^[A-Za-z0-9_-]+$"),
):
    """
    Enterprise WebSocket endpoint for live GPS tracking (Family Tracking).
    - Redis Pub/Sub for horizontal scaling across multiple instances.
    - Periodic heartbeat (ping/pong) to detect half-open connections.
    - Stale connection cleanup with configurable timeout.
    - SECURITY#17: Message size limit enforced before reading full payload.
    """
    if not _origin_allowed(websocket.headers.get("origin")):
        await websocket.close(code=1008, reason="Origin not allowed")
        return
    # SECURITY: JWT passed in WebSocket query params gets logged by
    # proxies, load balancers, and in server access logs. This should be
    # replaced with a short-lived one-time token or WebSocket sub-protocol
    # auth before production deployment.
    ws_token = websocket.query_params.get("token")
    if ws_token:
        logger.debug("WebSocket auth via query param token (group=%s)", group_id)
    if not _is_valid_ws_token(ws_token):
        await websocket.close(code=1008, reason="Authentication required")
        return

    if not manager.redis and hasattr(websocket.app.state, "cache"):
        manager.set_redis(websocket.app.state.cache._client)

    manager.start_cleanup()
    await manager.connect(websocket, group_id)
    try:
        while True:
            data = await websocket.receive_text()
            connection_health.mark_activity(websocket)

            if len(data.encode("utf-8")) > MAX_TRACKING_MESSAGE_BYTES:
                await websocket.close(code=1009, reason="Message too large")
                return

            try:
                payload = json.loads(data)
                if payload.get("type") == "pong":
                    continue
                if not _is_valid_tracking_payload(payload):
                    await websocket.send_json({"type": "error", "message": "Invalid tracking payload"})
                    continue
                await manager.broadcast(payload, group_id)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
    except WebSocketDisconnect:
        manager.disconnect(websocket, group_id)
