# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for core/audit.py — AuditLog, AuditEvent, and structured audit logging."""

from __future__ import annotations

import json
import logging

from core.audit import AuditEvent, AuditLog


class TestAuditEvent:
    def test_event_values(self):
        assert AuditEvent.AUTH_LOGIN == "auth.login"
        assert AuditEvent.AUTH_LOGOUT == "auth.logout"
        assert AuditEvent.AUTH_FAILED == "auth.failed"
        assert AuditEvent.PROFILE_UPDATE == "profile.update"
        assert AuditEvent.SOS_TRIGGER == "sos.trigger"
        assert AuditEvent.SOS_OFFLINE_QUEUED == "sos.offline_queued"
        assert AuditEvent.ROAD_REPORT_SUBMITTED == "road.report.submitted"
        assert AuditEvent.CHATBOT_QUERY == "chatbot.query"
        assert AuditEvent.ADMIN_ACTION == "admin.action"
        assert AuditEvent.INDEX_REBUILD == "index.rebuild"
        assert AuditEvent.API_KEY_ROTATED == "api.key.rotated"

    def test_event_is_enum(self):
        assert AuditEvent.AUTH_LOGIN in AuditEvent
        assert "auth.login" in AuditEvent._value2member_map_

    def test_all_events_have_unique_values(self):
        values = [e.value for e in AuditEvent]
        assert len(values) == len(set(values))


class TestAuditLog:
    def test_log_emits_json(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log(
                AuditEvent.AUTH_LOGIN,
                user_id="user-123",
                ip_address="192.168.1.1",
                details={"operator_name": "test-op"},
            )
        assert len(caplog.records) >= 1
        record = caplog.records[0]
        payload = json.loads(record.getMessage())
        assert payload["event"] == "auth.login"
        assert payload["user_id"] == "user-123"
        assert payload["ip_address"] == "192.168.1.1"
        assert payload["success"] is True
        assert payload["details"]["operator_name"] == "test-op"

    def test_log_without_details(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log(
                AuditEvent.AUTH_LOGOUT,
                user_id="user-456",
                ip_address="10.0.0.1",
            )
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["event"] == "auth.logout"
        assert payload["details"] == {}

    def test_log_with_failure(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log(
                AuditEvent.AUTH_FAILED,
                user_id="attacker@evil.com",
                ip_address="203.0.113.1",
                details={"reason": "invalid_password"},
                success=False,
            )
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["success"] is False
        assert payload["details"]["reason"] == "invalid_password"

    def test_log_without_user_id(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log(
                AuditEvent.SOS_TRIGGER,
                ip_address="10.0.0.5",
                details={"lat": 13.0, "lon": 80.0},
            )
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["user_id"] is None

    def test_log_timestamp_iso_format(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log(
                AuditEvent.AUTH_LOGIN,
                user_id="u1",
                ip_address="::1",
            )
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert "T" in payload["timestamp"]
        # Should be ISO 8601 format
        assert len(payload["timestamp"]) > 10


class TestAuditLogStaticMethods:
    def test_log_auth_login(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log_auth_login("user-op", "10.0.0.2", "Operator One")
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["event"] == "auth.login"
        assert payload["user_id"] == "user-op"
        assert payload["details"]["operator_name"] == "Operator One"

    def test_log_auth_failed(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log_auth_failed("unknown@test.com", "10.0.0.3", "invalid_password_db")
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["event"] == "auth.failed"
        assert payload["success"] is False
        assert payload["details"]["reason"] == "invalid_password_db"

    def test_log_sos_trigger(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log_sos_trigger("user-999", 13.0827, 80.2707, ip_address="10.0.0.4")
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["event"] == "sos.trigger"
        assert payload["details"]["lat"] == 13.0827
        assert payload["details"]["lon"] == 80.2707

    def test_log_sos_trigger_no_user(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log_sos_trigger(None, 12.0, 77.0)
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["user_id"] is None
        assert payload["details"]["lat"] == 12.0

    def test_log_admin_action(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log_admin_action(
                "admin-1",
                "complaint_assigned",
                ip_address="10.0.0.5",
                details={"complaint_ref": "CMP-123", "officer_id": "OFF-456"},
            )
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["event"] == "admin.action"
        assert payload["details"]["action"] == "complaint_assigned"
        assert payload["details"]["complaint_ref"] == "CMP-123"

    def test_log_admin_action_no_details(self, caplog):
        caplog.set_level(logging.INFO)
        with caplog.at_level(logging.INFO):
            AuditLog.log_admin_action("admin-2", "data_cleanup", ip_address="10.0.0.6")
        record = caplog.records[-1]
        payload = json.loads(record.getMessage())
        assert payload["event"] == "admin.action"
        assert payload["details"]["action"] == "data_cleanup"
