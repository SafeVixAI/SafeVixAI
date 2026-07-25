# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Role-Based Access Control (RBAC) for SafeVixAI Backend.

Defines user roles, permission checks, and FastAPI dependencies for
enforcing role-based access on protected endpoints.

Roles:
    - admin: Full system access, including admin endpoints and user management.
    - operator: Can trigger SOS, manage road reports, and access operational tools.
    - user: Standard authenticated user with access to core features.
    - readonly: Read-only access to public data and emergency information.
"""
from __future__ import annotations

from enum import StrEnum

from fastapi import Depends, HTTPException


class Role(StrEnum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    OPERATOR = "operator"
    FIELD_OFFICER = "field_officer"
    USER = "user"
    READONLY = "readonly"


ROLE_HIERARCHY = {
    Role.ADMIN: [Role.ADMIN, Role.OPERATOR, Role.FIELD_OFFICER, Role.USER, Role.READONLY],
    Role.OPERATOR: [Role.OPERATOR, Role.FIELD_OFFICER, Role.USER, Role.READONLY],
    Role.FIELD_OFFICER: [Role.FIELD_OFFICER, Role.USER, Role.READONLY],
    Role.USER: [Role.USER, Role.READONLY],
    Role.READONLY: [Role.READONLY],
}


def _has_permission(user_role: str, required_role: Role) -> bool:
    try:
        role_enum = Role(user_role)
    except ValueError:
        return False
    allowed_roles = ROLE_HIERARCHY.get(role_enum, [])
    return required_role in allowed_roles


def require_role(required_role: Role):
    from core.security import get_current_user
    async def dependency(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role", Role.READONLY.value)
        if not _has_permission(user_role, required_role):
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required role: {required_role.value}",
            )
        return user
    return dependency
