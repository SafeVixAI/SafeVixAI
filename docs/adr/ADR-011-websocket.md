# ADR-011: WebSocket-Based Live Family Tracking

**Date:** 2026-06-22
**Status:** ✅ Accepted
**Author:** SafeVixAI Backend Team

## Context

The SOS feature requires real-time location sharing with family members. The tracked user's location must update continuously (every 5-10 seconds) during an active SOS session. Polling REST endpoints would be inefficient and introduce significant latency.

## Options Considered

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **WebSocket (chosen)** | Persistent bidirectional connection via `ws://` | < 1s latency, efficient, bidirectional | Connection management, scaling complexity |
| **Server-Sent Events** | Unidirectional event stream from server | Simpler than WS, HTTP-based | One-direction only (no client→server), browser limits |
| **Polling** | REST GET every 5 seconds | Simple | ~60x more HTTP requests, 5s latency |
| **WebRTC** | Peer-to-peer data channel | Lowest latency | Complex signaling, STUN/TURN needed |

## Decision

Implement a WebSocket server at `/api/v1/tracking/{group_id}`:
- Created when SOS is activated — unique `tracking_group_id` returned
- Sender (sos user): pushes GPS + battery + speed every 5 seconds
- Receivers (family): real-time location feed with map markers
- WebSocket events: `location_update`, `sos_status_change`, `connection_health`
- 60s heartbeat to detect disconnection
- Session timeout after 4 hours of inactivity

## Consequences

- Real-time tracking with sub-second latency
- Server must maintain WebSocket connections (~1KB per connection)
- For horizontal scaling, use Redis PubSub to broadcast across instances
- Family tracking works without any app installation (receivers view via browser)
- WebSocket connection requires HTTPS in production (WSS)
