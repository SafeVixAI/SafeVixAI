# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""WebSocket manager for real-time notification delivery with heartbeat and reconnect."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from models.notification import Notification

logger = logging.getLogger(__name__)

HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 10
MAX_RECONNECT_DELAY = 30


class NotificationManager:
    """Manages WebSocket connections for real-time notification streaming.

    Features:
    - Per-user connection pools with session tracking
    - Heartbeat ping/pong every 30s with 10s timeout
    - Exponential backoff guidance for client reconnect
    - Broadcast to all users or specific user lists
    """

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}
        self._sessions: dict[str, str] = {}
        self._last_pong: dict[str, float] = {}
        self._heartbeat_tasks: dict[str, asyncio.Task] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        if user_id not in self._connections:
            self._connections[user_id] = set()
        self._connections[user_id].add(websocket)
        session_id = str(uuid.uuid4())
        ws_key = str(id(websocket))
        self._sessions[ws_key] = session_id
        self._last_pong[ws_key] = asyncio.get_event_loop().time()
        logger.debug('Notification WS connected: user=%s session=%s', user_id, session_id)
        await websocket.send_json({
            'type': 'connected',
            'session_id': session_id,
            'user_id': user_id,
            'heartbeat_interval': HEARTBEAT_INTERVAL,
        })
        self._heartbeat_tasks[ws_key] = asyncio.create_task(
            self._heartbeat_loop(websocket, ws_key, user_id)
        )

    async def _heartbeat_loop(self, websocket: WebSocket, ws_key: str, user_id: str) -> None:
        """Send periodic pings and disconnect if no pong received."""
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                now = asyncio.get_event_loop().time()
                last = self._last_pong.get(ws_key, now)
                if now - last > HEARTBEAT_INTERVAL + HEARTBEAT_TIMEOUT:
                    logger.warning(
                        'Notification WS heartbeat timeout: user=%s session=%s',
                        user_id, self._sessions.get(ws_key),
                    )
                    await websocket.close(code=1000)
                    break
                try:
                    await websocket.send_json({'type': 'ping'})
                except Exception:
                    break
        except asyncio.CancelledError:
            pass
        except Exception:
            pass

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        ws_key = str(id(websocket))
        self._sessions.pop(ws_key, None)
        self._last_pong.pop(ws_key, None)
        task = self._heartbeat_tasks.pop(ws_key, None)
        if task:
            task.cancel()
        if user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        logger.debug('Notification WS disconnected: user=%s', user_id)

    async def send_notification(
        self,
        user_id: str,
        notification: Notification,
    ) -> int:
        """Send a notification to all active connections for a user."""
        if user_id not in self._connections:
            return 0
        payload = self._build_payload(notification)
        sent = 0
        dead: list[WebSocket] = []
        for ws in self._connections[user_id]:
            try:
                await ws.send_json(payload)
                sent += 1
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections[user_id].discard(ws)
        if not self._connections[user_id]:
            del self._connections[user_id]
        return sent

    async def broadcast(
        self,
        notification: Notification,
        user_ids: list[str] | None = None,
    ) -> int:
        """Broadcast a notification to all users or a specific list."""
        if user_ids:
            total = 0
            for uid in user_ids:
                total += await self.send_notification(uid, notification)
            return total
        total = 0
        for uid in list(self._connections.keys()):
            total += await self.send_notification(uid, notification)
        return total

    async def broadcast_event(
        self,
        event_type: str,
        data: dict[str, Any],
        user_ids: list[str] | None = None,
    ) -> int:
        """Broadcast a generic event to connected clients."""
        payload = {'type': event_type, **data}
        if user_ids:
            total = 0
            for uid in user_ids:
                if uid in self._connections:
                    for ws in list(self._connections[uid]):
                        try:
                            await ws.send_json(payload)
                            total += 1
                        except Exception:
                            pass
            return total
        total = 0
        for uid in list(self._connections.keys()):
            for ws in list(self._connections[uid]):
                try:
                    await ws.send_json(payload)
                    total += 1
                except Exception:
                    pass
        return total

    def get_connection_count(self, user_id: str | None = None) -> int:
        if user_id:
            return len(self._connections.get(user_id, set()))
        return sum(len(ws) for ws in self._connections.values())

    def get_connected_users(self) -> list[str]:
        return list(self._connections.keys())

    async def handle_websocket(self, websocket: WebSocket, user_id: str) -> None:
        await self.connect(websocket, user_id)
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                    msg_type = msg.get('type', 'ping')
                    if msg_type == 'pong':
                        self._last_pong[str(id(websocket))] = asyncio.get_event_loop().time()
                    elif msg_type == 'ack':
                        logger.debug('Notification ack: user=%s msg=%s', user_id, msg.get('notification_id'))
                    elif msg_type == 'mark_read':
                        logger.debug('Mark read: user=%s notification=%s', user_id, msg.get('notification_id'))
                    elif msg_type == 'reconnect':
                        max_delay = msg.get('max_delay', MAX_RECONNECT_DELAY)
                        await websocket.send_json({
                            'type': 'reconnect_info',
                            'delay': min(max_delay, MAX_RECONNECT_DELAY),
                            'user_id': user_id,
                        })
                except json.JSONDecodeError:
                    pass
        except WebSocketDisconnect:
            pass
        except Exception as exc:
            logger.warning('Notification WS error user=%s: %s', user_id, exc)
        finally:
            await self.disconnect(websocket, user_id)

    def _build_payload(self, notification: Notification) -> dict[str, Any]:
        return {
            'type': 'notification',
            'id': str(notification.id),
            'channel': notification.channel.value if notification.channel else None,
            'category': notification.category.value if notification.category else None,
            'priority': notification.priority.value if notification.priority else 'normal',
            'title': notification.title,
            'body': notification.body,
            'metadata': notification.payload,
            'source': notification.source,
            'correlation_id': notification.correlation_id,
            'created_at': notification.created_at.isoformat() if notification.created_at else None,
        }


notification_manager = NotificationManager()
