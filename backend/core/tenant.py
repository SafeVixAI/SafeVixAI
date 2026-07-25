# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tenant isolation utilities for SafeVixAI Backend.

Provides:
- Tenant ID extraction from authenticated user
- Tenant-aware query filtering
- Multi-tenant data isolation helpers

Phase 0.6: Prevents data leakage between tenants.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import Request
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import get_current_user_optional

logger = logging.getLogger(__name__)

# Tables that should be filtered by org_id
TENANT_AWARE_TABLES = {
    "users",
    "user_profiles",
    "emergency_services",
    "road_issues",
    "road_infrastructure",
    "sos_incidents",
}


async def get_tenant_id(request: Request) -> str | None:
    """Extract tenant ID from authenticated user."""
    user = await get_current_user_optional(request)
    if user:
        return user.get("org_id")
    return None


def apply_tenant_filter(session: AsyncSession, tenant_id: str | None) -> None:
    """Apply tenant filter to all queries in the session.

    This uses SQLAlchemy 2.0 event listeners to automatically add
    org_id filters to queries on tenant-aware tables via do_orm_execute.
    """
    if not tenant_id:
        return

    @event.listens_for(session, "do_orm_execute")
    def _do_orm_execute(orm_execute_state):
        if not orm_execute_state.is_select or not orm_execute_state.is_orm_statement:
            return
        for mapper in orm_execute_state.all_mappers:
            table_name = mapper.class_.__tablename__
            if table_name in TENANT_AWARE_TABLES and hasattr(mapper.class_, "org_id"):
                orm_execute_state.statement = orm_execute_state.statement.where(
                    mapper.class_.org_id == tenant_id
                )


class TenantAwareQuery:
    """Helper class for tenant-aware database queries.

    Usage:
        async with AsyncSessionLocal() as session:
            query = TenantAwareQuery(session, tenant_id)
            results = await query.execute(select(User))
    """

    def __init__(self, session: AsyncSession, tenant_id: str | None) -> None:
        self.session = session
        self.tenant_id = tenant_id

    def filter_by_tenant(self, stmt: Any) -> Any:
        """Add org_id filter to a SQLAlchemy statement."""
        if not self.tenant_id:
            return stmt

        # Get the entity from the statement
        if hasattr(stmt, 'column_descriptions'):
            for desc in stmt.column_descriptions:
                entity = desc.get('entity')
                if entity and hasattr(entity, '__tablename__'):
                    table_name = entity.__tablename__
                    if table_name in TENANT_AWARE_TABLES and hasattr(entity, 'org_id'):
                        stmt = stmt.where(entity.org_id == self.tenant_id)

        return stmt

    async def execute(self, stmt: Any) -> Any:
        """Execute a statement with tenant filtering applied."""
        filtered_stmt = self.filter_by_tenant(stmt)
        return await self.session.execute(filtered_stmt)
