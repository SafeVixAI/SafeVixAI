# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for tenant isolation utilities."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from core.tenant import (
    TENANT_AWARE_TABLES,
    TenantAwareQuery,
    apply_tenant_filter,
    get_tenant_id,
)


def test_tenant_aware_tables_defined():
    """Test that tenant-aware tables are properly defined."""
    assert isinstance(TENANT_AWARE_TABLES, set)
    assert 'users' in TENANT_AWARE_TABLES
    assert 'user_profiles' in TENANT_AWARE_TABLES
    assert 'emergency_services' in TENANT_AWARE_TABLES
    assert 'road_issues' in TENANT_AWARE_TABLES
    assert 'road_infrastructure' in TENANT_AWARE_TABLES
    assert 'sos_incidents' in TENANT_AWARE_TABLES


@pytest.mark.asyncio
async def test_get_tenant_id_with_user():
    """Test extracting tenant ID from authenticated user."""
    mock_request = MagicMock(spec=Request)

    with patch('core.tenant.get_current_user_optional', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {
            'id': 'user123',
            'org_id': 'org_456',
            'email': 'user@example.com',
        }

        tenant_id = await get_tenant_id(mock_request)

        assert tenant_id == 'org_456'
        mock_get_user.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_get_tenant_id_without_user():
    """Test extracting tenant ID when no user is authenticated."""
    mock_request = MagicMock(spec=Request)

    with patch('core.tenant.get_current_user_optional', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = None

        tenant_id = await get_tenant_id(mock_request)

        assert tenant_id is None
        mock_get_user.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_get_tenant_id_user_without_org():
    """Test extracting tenant ID when user has no org_id."""
    mock_request = MagicMock(spec=Request)

    with patch('core.tenant.get_current_user_optional', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = {
            'id': 'user123',
            'email': 'user@example.com',
            # No org_id
        }

        tenant_id = await get_tenant_id(mock_request)

        assert tenant_id is None


def test_apply_tenant_filter_no_tenant():
    """Test that no filter is applied when tenant_id is None."""
    mock_session = MagicMock(spec=AsyncSession)

    # Should return early without adding any listeners
    apply_tenant_filter(mock_session, None)

    # Verify no event listeners were added
    # (This is hard to test directly, but we can verify the function doesn't crash)


def test_apply_tenant_filter_with_tenant():
    """Test that tenant filter is applied when tenant_id is provided."""
    from sqlalchemy import Column, Integer, String, create_engine, select
    from sqlalchemy.orm import Session, declarative_base

    Base = declarative_base()

    class TestUser(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        org_id = Column(String)

    engine = create_engine('sqlite://', echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        session.add_all([
            TestUser(name='alice', org_id='org_1'),
            TestUser(name='bob', org_id='org_2'),
            TestUser(name='charlie', org_id='org_1'),
        ])
        session.commit()

    with Session(engine) as session:
        apply_tenant_filter(session, 'org_1')
        users = session.execute(select(TestUser)).scalars().all()
        names = [u.name for u in users]
        assert names == ['alice', 'charlie'], f"Expected org_1 users, got {names}"

    with Session(engine) as session:
        apply_tenant_filter(session, 'org_2')
        users = session.execute(select(TestUser)).scalars().all()
        names = [u.name for u in users]
        assert names == ['bob'], f"Expected org_2 users, got {names}"


def test_tenant_aware_query_init():
    """Test TenantAwareQuery initialization."""
    mock_session = MagicMock(spec=AsyncSession)

    query = TenantAwareQuery(mock_session, 'org_456')

    assert query.session == mock_session
    assert query.tenant_id == 'org_456'


def test_tenant_aware_query_init_no_tenant():
    """Test TenantAwareQuery initialization without tenant."""
    mock_session = MagicMock(spec=AsyncSession)

    query = TenantAwareQuery(mock_session, None)

    assert query.session == mock_session
    assert query.tenant_id is None


def test_filter_by_tenant_no_tenant():
    """Test that no filter is added when tenant_id is None."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = []

    query = TenantAwareQuery(mock_session, None)
    result = query.filter_by_tenant(mock_stmt)

    # Should return the same statement unchanged
    assert result == mock_stmt


def test_filter_by_tenant_with_tenant():
    """Test that tenant filter is added when tenant_id is provided."""
    mock_session = MagicMock(spec=AsyncSession)

    # Create a mock entity with org_id
    mock_entity = MagicMock()
    mock_entity.__tablename__ = 'users'
    mock_entity.org_id = MagicMock()

    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = [
        {'entity': mock_entity}
    ]
    mock_stmt.where.return_value = mock_stmt

    query = TenantAwareQuery(mock_session, 'org_456')
    query.filter_by_tenant(mock_stmt)

    # Verify where clause was called with org_id filter
    mock_stmt.where.assert_called_once()
    # The exact assertion depends on how SQLAlchemy constructs the filter


def test_filter_by_tenant_non_tenant_aware_table():
    """Test that no filter is added for non-tenant-aware tables."""
    mock_session = MagicMock(spec=AsyncSession)

    # Create a mock entity that's not tenant-aware
    mock_entity = MagicMock()
    mock_entity.__tablename__ = 'some_other_table'
    mock_entity.org_id = MagicMock()

    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = [
        {'entity': mock_entity}
    ]

    query = TenantAwareQuery(mock_session, 'org_456')
    query.filter_by_tenant(mock_stmt)

    # Verify where clause was NOT called
    mock_stmt.where.assert_not_called()


def test_filter_by_tenant_entity_without_org_id():
    """Test that no filter is added when entity doesn't have org_id."""
    mock_session = MagicMock(spec=AsyncSession)

    # Create a mock entity without org_id
    mock_entity = MagicMock()
    mock_entity.__tablename__ = 'users'
    del mock_entity.org_id  # Remove org_id attribute

    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = [
        {'entity': mock_entity}
    ]

    query = TenantAwareQuery(mock_session, 'org_456')
    query.filter_by_tenant(mock_stmt)

    # Verify where clause was NOT called
    mock_stmt.where.assert_not_called()


def test_filter_by_tenant_entity_without_tablename():
    """Test that no filter is added when entity doesn't have __tablename__."""
    mock_session = MagicMock(spec=AsyncSession)

    # Create a mock entity without __tablename__
    mock_entity = MagicMock()
    del mock_entity.__tablename__
    mock_entity.org_id = MagicMock()

    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = [
        {'entity': mock_entity}
    ]

    query = TenantAwareQuery(mock_session, 'org_456')
    query.filter_by_tenant(mock_stmt)

    # Verify where clause was NOT called
    mock_stmt.where.assert_not_called()


def test_filter_by_tenant_empty_column_descriptions():
    """Test that no filter is added when column_descriptions is empty."""
    mock_session = MagicMock(spec=AsyncSession)

    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = []

    query = TenantAwareQuery(mock_session, 'org_456')
    query.filter_by_tenant(mock_stmt)

    # Verify where clause was NOT called
    mock_stmt.where.assert_not_called()


def test_filter_by_tenant_entity_is_none():
    """Test that no filter is added when entity is None."""
    mock_session = MagicMock(spec=AsyncSession)

    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = [
        {'entity': None}
    ]

    query = TenantAwareQuery(mock_session, 'org_456')
    query.filter_by_tenant(mock_stmt)

    # Verify where clause was NOT called
    mock_stmt.where.assert_not_called()


@pytest.mark.asyncio
async def test_tenant_aware_query_execute():
    """Test executing a statement with tenant filtering."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()

    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = []
    mock_stmt.where.return_value = mock_stmt

    query = TenantAwareQuery(mock_session, 'org_456')
    await query.execute(mock_stmt)

    # Verify execute was called with the filtered statement
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_tenant_aware_query_execute_no_tenant():
    """Test executing a statement without tenant filtering."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_session.execute = AsyncMock()

    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = []

    query = TenantAwareQuery(mock_session, None)
    await query.execute(mock_stmt)

    # Verify execute was called
    mock_session.execute.assert_called_once()


def test_all_tenant_aware_tables_have_org_id():
    """Test that all tenant-aware tables are expected to have org_id."""
    expected_tables = {
        'users',
        'user_profiles',
        'emergency_services',
        'road_issues',
        'road_infrastructure',
        'sos_incidents',
    }

    assert expected_tables == TENANT_AWARE_TABLES


def test_tenant_aware_query_with_multiple_entities():
    """Test filtering with multiple entities in column_descriptions."""
    mock_session = MagicMock(spec=AsyncSession)
    mock_user_entity = MagicMock()
    mock_user_entity.__tablename__ = 'users'
    mock_user_entity.org_id = MagicMock()
    mock_other_entity = MagicMock()
    mock_other_entity.__tablename__ = 'some_other_table'
    mock_other_entity.org_id = MagicMock()
    mock_stmt = MagicMock()
    mock_stmt.column_descriptions = [
        {'entity': mock_user_entity},
        {'entity': mock_other_entity},
    ]
    mock_stmt.where.return_value = mock_stmt
    query = TenantAwareQuery(mock_session, 'org_456')
    query.filter_by_tenant(mock_stmt)
    assert mock_stmt.where.call_count == 1


def test_do_orm_execute_skips_non_select():
    """do_orm_execute should skip non-SELECT statements (line 57 branch)."""
    from sqlalchemy import Column, Integer, String, create_engine, update
    from sqlalchemy.orm import Session, declarative_base

    from core.tenant import apply_tenant_filter
    Base = declarative_base()
    class TestUser(Base):
        __tablename__ = 'users'
        id = Column(Integer, primary_key=True)
        name = Column(String)
        org_id = Column(String)
    engine = create_engine('sqlite://', echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        apply_tenant_filter(session, 'org_1')
        session.add(TestUser(name='dave', org_id='org_2'))
        session.flush()
        stmt = update(TestUser).where(TestUser.name == 'dave').values(name='dave2')
        session.execute(stmt)
        session.commit()


def test_do_orm_execute_skips_non_tenant_aware():
    """do_orm_execute should skip non-tenant-aware tables (line 57 else branch)."""
    from sqlalchemy import Column, Integer, String, create_engine, select
    from sqlalchemy.orm import Session, declarative_base

    from core.tenant import apply_tenant_filter
    Base = declarative_base()
    class NonTenantTable(Base):
        __tablename__ = 'non_tenant_table'
        id = Column(Integer, primary_key=True)
        name = Column(String)
    engine = create_engine('sqlite://', echo=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        apply_tenant_filter(session, 'org_1')
        session.add(NonTenantTable(name='test'))
        session.flush()
        rows = session.execute(select(NonTenantTable)).scalars().all()
        assert len(rows) == 1
        session.commit()
