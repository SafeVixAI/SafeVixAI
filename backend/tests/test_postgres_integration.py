# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Enterprise integration tests using testcontainers-postgres with PostGIS.

Requires Docker to be running locally. Skipped automatically in CI-less envs.
"""

import os

import pytest
from sqlalchemy import create_engine, text

try:
    from testcontainers.postgres import PostgresContainer
except ModuleNotFoundError:
    PostgresContainer = None  # type: ignore[assignment]

pytestmark = pytest.mark.skipif(
    not os.environ.get("CI") or PostgresContainer is None,
    reason="requires Docker + testcontainers for testcontainers-postgres",
)


class TestPostgresIntegration:
    """End-to-end PostGIS integration via testcontainers."""

    @pytest.fixture(scope="class")
    def pg_container(self):
        with PostgresContainer("postgis/postgis:16-3.4") as pg:
            yield pg

    def test_basic_connection(self, pg_container):
        engine = create_engine(pg_container.get_connection_url())
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 AS val"))
            assert result.scalar() == 1

    def test_postgis_extension(self, pg_container):
        engine = create_engine(pg_container.get_connection_url())
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT PostGIS_Version()")
            )
            version = result.scalar()
            assert version is not None
            assert "3." in version

    def test_st_makepoint(self, pg_container):
        engine = create_engine(pg_container.get_connection_url())
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT ST_AsText(ST_MakePoint(:lon, :lat))"),
                {"lon": 80.2707, "lat": 13.0827},
            )
            assert result.scalar() == "POINT(80.2707 13.0827)"

    def test_st_dwithin_geography(self, pg_container):
        engine = create_engine(pg_container.get_connection_url())
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT ST_DWithin(
                        ST_MakePoint(:lon1, :lat1)::geography,
                        ST_MakePoint(:lon2, :lat2)::geography,
                        :radius
                    )
                """),
                {"lon1": 80.2707, "lat1": 13.0827,
                 "lon2": 80.2800, "lat2": 13.0900,
                 "radius": 2000},
            )
            assert result.scalar() is True

    def test_st_dwithin_outside_radius(self, pg_container):
        engine = create_engine(pg_container.get_connection_url())
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT ST_DWithin(
                        ST_MakePoint(:lon1, :lat1)::geography,
                        ST_MakePoint(:lon2, :lat2)::geography,
                        :radius
                    )
                """),
                {"lon1": 80.2707, "lat1": 13.0827,
                 "lon2": 80.5000, "lat2": 13.3000,
                 "radius": 100},
            )
            assert result.scalar() is False

    def test_gin_index_on_geography(self, pg_container):
        engine = create_engine(pg_container.get_connection_url())
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.execute(text("""
                CREATE TABLE test_issues (
                    id SERIAL PRIMARY KEY,
                    location geography(Point, 4326)
                )
            """))
            conn.execute(text("""
                CREATE INDEX idx_test_location
                ON test_issues USING GIST (location)
            """))
            conn.commit()
            result = conn.execute(text("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'test_issues'
                AND indexname = 'idx_test_location'
            """))
            assert result.scalar() == "idx_test_location"

    def test_bulk_insert_and_spatial_query(self, pg_container):
        engine = create_engine(pg_container.get_connection_url())
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.execute(text("""
                CREATE TABLE test_hospitals (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    location geography(Point, 4326)
                )
            """))
            conn.execute(text("""
                INSERT INTO test_hospitals (name, location) VALUES
                ('Hospital A', ST_MakePoint(80.2707, 13.0827)::geography),
                ('Hospital B', ST_MakePoint(80.2800, 13.0900)::geography),
                ('Hospital C', ST_MakePoint(80.5000, 13.3000)::geography)
            """))
            conn.commit()
            result = conn.execute(
                text("""
                    SELECT name FROM test_hospitals
                    WHERE ST_DWithin(
                        location,
                        ST_MakePoint(80.2707, 13.0827)::geography,
                        2000
                    )
                    ORDER BY name
                """),
            )
            rows = result.fetchall()
            names = [r[0] for r in rows]
            assert "Hospital A" in names
            assert "Hospital B" in names
            assert "Hospital C" not in names

    def test_asyncpg_connection_string(self, pg_container):
        url = pg_container.get_connection_url()
        async_url = url.replace("postgresql://", "postgresql+asyncpg://")
        assert "+asyncpg" in async_url
        assert "localhost" in async_url or "127.0.0.1" in async_url
