# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import json
from unittest.mock import patch

from core.audit import AuditEvent, AuditLog


class TestAuditEvent:
    def test_enum_values(self) -> None:
        assert AuditEvent.AUTH_LOGIN.value == "auth.login"
        assert AuditEvent.PROFILE_UPDATE.value == "profile.update"
        assert AuditEvent.SOS_TRIGGER.value == "sos.trigger"


class TestAuditLog:
    def test_log_basic(self) -> None:
        with patch("core.audit.logger") as mock_log:
            AuditLog.log(AuditEvent.AUTH_LOGIN, user_id="user1", ip_address="127.0.0.1")
            mock_log.info.assert_called_once()
            payload = json.loads(mock_log.info.call_args[0][0])
            assert payload["event"] == "auth.login"
            assert payload["user_id"] == "user1"
            assert payload["ip_address"] == "127.0.0.1"
            assert payload["success"] is True

    def test_log_with_details(self) -> None:
        with patch("core.audit.logger") as mock_log:
            AuditLog.log(AuditEvent.PROFILE_UPDATE, user_id="user1", details={"field": "name"})
            payload = json.loads(mock_log.info.call_args[0][0])
            assert payload["details"]["field"] == "name"

    def test_log_failed_event(self) -> None:
        with patch("core.audit.logger") as mock_log:
            AuditLog.log(AuditEvent.AUTH_FAILED, user_id="user1", success=False, details={"reason": "bad pass"})
            payload = json.loads(mock_log.info.call_args[0][0])
            assert payload["success"] is False
            assert payload["details"]["reason"] == "bad pass"

    def test_log_auth_login(self) -> None:
        with patch.object(AuditLog, "log") as mock_log:
            AuditLog.log_auth_login("user1", "10.0.0.1", "Operator A")
            mock_log.assert_called_once_with(
                AuditEvent.AUTH_LOGIN, user_id="user1", ip_address="10.0.0.1",
                details={"operator_name": "Operator A"},
            )

    def test_log_auth_failed(self) -> None:
        with patch.object(AuditLog, "log") as mock_log:
            AuditLog.log_auth_failed("user1", "10.0.0.1", "wrong password")
            mock_log.assert_called_once_with(
                AuditEvent.AUTH_FAILED, user_id="user1", ip_address="10.0.0.1",
                details={"reason": "wrong password"}, success=False,
            )

    def test_log_sos_trigger(self) -> None:
        with patch.object(AuditLog, "log") as mock_log:
            AuditLog.log_sos_trigger("user1", 13.08, 80.27, ip_address="10.0.0.1")
            mock_log.assert_called_once_with(
                AuditEvent.SOS_TRIGGER, user_id="user1", ip_address="10.0.0.1",
                details={"lat": 13.08, "lon": 80.27},
            )

    def test_log_sos_trigger_no_ip(self) -> None:
        with patch.object(AuditLog, "log") as mock_log:
            AuditLog.log_sos_trigger(None, 13.08, 80.27)
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["user_id"] is None

    def test_log_admin_action(self) -> None:
        with patch.object(AuditLog, "log") as mock_log:
            AuditLog.log_admin_action("admin1", "rebuild_index", ip_address="10.0.0.1")
            mock_log.assert_called_once_with(
                AuditEvent.ADMIN_ACTION, user_id="admin1", ip_address="10.0.0.1",
                details={"action": "rebuild_index"},
            )

    def test_log_admin_action_with_details(self) -> None:
        with patch.object(AuditLog, "log") as mock_log:
            AuditLog.log_admin_action("admin1", "purge_cache", details={"cache": "redis"})
            mock_log.assert_called_once()
            assert mock_log.call_args[1]["details"]["cache"] == "redis"
