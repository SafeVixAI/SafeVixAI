# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

# backend/core/audit.py — Tamper-proof audit logging for sensitive operations
# SECURITY FIX: Audit log for auth events, profile changes, SOS events

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

logger = logging.getLogger("safevixai.audit")


class AuditEvent(StrEnum):
    AUTH_LOGIN = "auth.login"
    AUTH_LOGOUT = "auth.logout"
    AUTH_FAILED = "auth.failed"
    PROFILE_UPDATE = "profile.update"
    SOS_TRIGGER = "sos.trigger"
    SOS_OFFLINE_QUEUED = "sos.offline_queued"
    ROAD_REPORT_SUBMITTED = "road.report.submitted"
    CHATBOT_QUERY = "chatbot.query"
    ADMIN_ACTION = "admin.action"
    INDEX_REBUILD = "index.rebuild"
    API_KEY_ROTATED = "api.key.rotated"


class AuditLog:
    """Write structured audit events to a dedicated log stream.

    In production, these logs should be shipped to a tamper-proof storage
    (e.g., S3 with Object Lock, or a dedicated audit log service).
    """

    @staticmethod
    def log(
        event: AuditEvent,
        *,
        user_id: str | None = None,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
        success: bool = True,
    ) -> None:
        payload = {
            "event": event.value,
            "timestamp": datetime.now(UTC).isoformat(),
            "user_id": user_id,
            "ip_address": ip_address,
            "success": success,
            "details": details or {},
        }
        logger.info(json.dumps(payload, ensure_ascii=False))

    @staticmethod
    def log_auth_login(user_id: str, ip_address: str, operator_name: str) -> None:
        AuditLog.log(
            AuditEvent.AUTH_LOGIN,
            user_id=user_id,
            ip_address=ip_address,
            details={"operator_name": operator_name},
        )

    @staticmethod
    def log_auth_failed(identifier: str, ip_address: str, reason: str) -> None:
        AuditLog.log(
            AuditEvent.AUTH_FAILED,
            user_id=identifier,
            ip_address=ip_address,
            details={"reason": reason},
            success=False,
        )

    @staticmethod
    def log_sos_trigger(
        user_id: str | None,
        lat: float,
        lon: float,
        ip_address: str | None = None,
    ) -> None:
        AuditLog.log(
            AuditEvent.SOS_TRIGGER,
            user_id=user_id,
            ip_address=ip_address,
            details={"lat": lat, "lon": lon},
        )

    @staticmethod
    def log_admin_action(
        user_id: str,
        action: str,
        ip_address: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        AuditLog.log(
            AuditEvent.ADMIN_ACTION,
            user_id=user_id,
            ip_address=ip_address,
            details={"action": action, **(details or {})},
        )
