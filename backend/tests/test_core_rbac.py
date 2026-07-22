# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for core/rbac.py — Role enum, role hierarchy, permission checks, require_role dependency."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from core.rbac import ROLE_HIERARCHY, Role, _has_permission, require_role


class TestRoleEnum:
    def test_role_values(self):
        assert Role.ADMIN.value == "admin"
        assert Role.OPERATOR.value == "operator"
        assert Role.FIELD_OFFICER.value == "field_officer"
        assert Role.USER.value == "user"
        assert Role.READONLY.value == "readonly"

    def test_role_is_string_enum(self):
        assert isinstance(Role.ADMIN, str)
        assert Role.ADMIN == "admin"

    def test_valid_role_from_string(self):
        assert Role("admin") is Role.ADMIN
        assert Role("user") is Role.USER
        assert Role("readonly") is Role.READONLY

    def test_invalid_role_from_string_raises(self):
        with pytest.raises(ValueError):
            Role("superadmin")


class TestRoleHierarchy:
    def test_admin_contains_all(self):
        hierarchy = ROLE_HIERARCHY[Role.ADMIN]
        assert Role.ADMIN in hierarchy
        assert Role.OPERATOR in hierarchy
        assert Role.FIELD_OFFICER in hierarchy
        assert Role.USER in hierarchy
        assert Role.READONLY in hierarchy

    def test_operator_contains_subset(self):
        hierarchy = ROLE_HIERARCHY[Role.OPERATOR]
        assert Role.ADMIN not in hierarchy
        assert Role.OPERATOR in hierarchy
        assert Role.FIELD_OFFICER in hierarchy
        assert Role.USER in hierarchy
        assert Role.READONLY in hierarchy

    def test_user_contains_limited(self):
        hierarchy = ROLE_HIERARCHY[Role.USER]
        assert Role.ADMIN not in hierarchy
        assert Role.OPERATOR not in hierarchy
        assert Role.USER in hierarchy
        assert Role.READONLY in hierarchy

    def test_readonly_only_self(self):
        hierarchy = ROLE_HIERARCHY[Role.READONLY]
        assert len(hierarchy) == 1
        assert hierarchy[0] is Role.READONLY

    def test_all_roles_in_hierarchy(self):
        for role in Role:
            assert role in ROLE_HIERARCHY, f"{role} missing from ROLE_HIERARCHY"


class TestHasPermission:
    def test_admin_has_admin_permission(self):
        assert _has_permission("admin", Role.ADMIN) is True

    def test_admin_has_operator_permission(self):
        assert _has_permission("admin", Role.OPERATOR) is True

    def test_operator_does_not_have_admin_permission(self):
        assert _has_permission("operator", Role.ADMIN) is False

    def test_user_has_user_permission(self):
        assert _has_permission("user", Role.USER) is True

    def test_user_does_not_have_operator_permission(self):
        assert _has_permission("user", Role.OPERATOR) is False

    def test_readonly_has_readonly_permission(self):
        assert _has_permission("readonly", Role.READONLY) is True

    def test_readonly_no_user_permission(self):
        assert _has_permission("readonly", Role.USER) is False

    def test_field_officer_has_readonly(self):
        assert _has_permission("field_officer", Role.READONLY) is True

    def test_field_officer_has_user(self):
        assert _has_permission("field_officer", Role.USER) is True

    def test_field_officer_no_operator(self):
        assert _has_permission("field_officer", Role.OPERATOR) is False

    def test_invalid_role_returns_false(self):
        assert _has_permission("nonexistent_role", Role.USER) is False

    def test_empty_role_returns_false(self):
        assert _has_permission("", Role.USER) is False


class TestRequireRoleDependency:
    """Tests for require_role dependency factory."""

    @pytest.mark.asyncio
    async def test_admin_role_allowed(self):
        dep = require_role(Role.ADMIN)
        user = {"sub": "admin-user", "role": "admin"}
        result = await dep(user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_admin_role_allows_operator(self):
        dep = require_role(Role.OPERATOR)
        user = {"sub": "admin-user", "role": "admin"}
        result = await dep(user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_operator_admins(self):
        dep = require_role(Role.ADMIN)
        user = {"sub": "op-user", "role": "operator"}
        with pytest.raises(HTTPException) as exc:
            await dep(user=user)
        assert exc.value.status_code == 403
        assert "Insufficient permissions" in exc.value.detail

    @pytest.mark.asyncio
    async def test_user_cannot_access_operator_endpoint(self):
        dep = require_role(Role.OPERATOR)
        user = {"sub": "user-1", "role": "user"}
        with pytest.raises(HTTPException) as exc:
            await dep(user=user)
        assert exc.value.status_code == 403
        assert "operator" in exc.value.detail.lower()

    @pytest.mark.asyncio
    async def test_readonly_cannot_access_user_endpoint(self):
        dep = require_role(Role.USER)
        user = {"sub": "ro-user", "role": "readonly"}
        with pytest.raises(HTTPException) as exc:
            await dep(user=user)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_role_defaults_to_readonly(self):
        dep = require_role(Role.READONLY)
        user = {"sub": "no-role"}
        result = await dep(user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_field_officer_allowed_for_operator_endpoint(self):
        dep = require_role(Role.FIELD_OFFICER)
        user = {"sub": "fo-user", "role": "field_officer"}
        result = await dep(user=user)
        assert result is user

    @pytest.mark.asyncio
    async def test_field_officer_no_admin(self):
        dep = require_role(Role.ADMIN)
        user = {"sub": "fo-user", "role": "field_officer"}
        with pytest.raises(HTTPException) as exc:
            await dep(user=user)
        assert exc.value.status_code == 403
