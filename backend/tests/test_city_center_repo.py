# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from services.city_center_repo import (
    _HARDCODED_CENTERS,
    _OFFLINE_CENTERS,
    get_all_city_centers,
    get_city_center,
    get_offline_centers,
)


class TestHardcodedCenters:
    def test_hardcoded_centers_has_major_cities(self) -> None:
        assert "chennai" in _HARDCODED_CENTERS
        assert "mumbai" in _HARDCODED_CENTERS
        assert "delhi" in _HARDCODED_CENTERS
        assert len(_HARDCODED_CENTERS) >= 47

    def test_hardcoded_centers_coords_are_valid(self) -> None:
        for slug, (lat, lon) in _HARDCODED_CENTERS.items():
            assert -90 <= lat <= 90, f"{slug}: lat {lat} out of range"
            assert -180 <= lon <= 180, f"{slug}: lon {lon} out of range"

    def test_offline_centers_subset_of_hardcoded(self) -> None:
        for slug in _OFFLINE_CENTERS:
            assert slug in _HARDCODED_CENTERS


class TestGetAllCityCenters:
    async def test_returns_hardcoded_when_no_db(self) -> None:
        result = await get_all_city_centers(db=None)
        assert result == _HARDCODED_CENTERS

    async def test_returns_db_results_when_available(self) -> None:
        db = MagicMock()
        row = MagicMock()
        row.city_slug = "testville"
        row.lat = 12.0
        row.lon = 77.0

        async def _mock_execute(*a, **kw):
            r = MagicMock()
            r.scalars.return_value.all.return_value = [row]
            return r

        db.execute.side_effect = _mock_execute
        result = await get_all_city_centers(db=db)
        assert result == {"testville": (12.0, 77.0)}

    async def test_falls_back_on_db_exception(self) -> None:
        db = MagicMock()
        db.execute.side_effect = Exception("DB down")
        result = await get_all_city_centers(db=db)
        assert result == _HARDCODED_CENTERS

    async def test_returns_hardcoded_when_db_empty(self) -> None:
        db = MagicMock()

        async def _mock_execute(*a, **kw):
            r = MagicMock()
            r.scalars.return_value.all.return_value = []
            return r

        db.execute.side_effect = _mock_execute
        result = await get_all_city_centers(db=db)
        assert result == _HARDCODED_CENTERS


class TestGetOfflineCenters:
    async def test_returns_offline_without_db(self) -> None:
        result = await get_offline_centers(db=None)
        assert result == _OFFLINE_CENTERS

    async def test_returns_db_offline_centers(self) -> None:
        db = MagicMock()
        row = MagicMock()
        row.city_slug = "chennai"
        row.lat = 13.08
        row.lon = 80.27

        async def _mock_execute(*a, **kw):
            r = MagicMock()
            r.scalars.return_value.all.return_value = [row]
            return r

        db.execute.side_effect = _mock_execute
        result = await get_offline_centers(db=db)
        assert "chennai" in result


class TestGetCityCenter:
    async def test_returns_coords_for_known_city(self) -> None:
        result = await get_city_center("chennai")
        assert result == (13.0827, 80.2707)

    async def test_returns_none_for_unknown_city(self) -> None:
        result = await get_city_center("nonexistentville")
        assert result is None

    async def test_uses_hardcoded_when_db_fails(self) -> None:
        db = MagicMock()
        db.execute.side_effect = Exception("DB down")
        result = await get_city_center("chennai", db=db)
        assert result == (13.0827, 80.2707)

    async def test_returns_db_result_when_available(self) -> None:
        db = MagicMock()
        row = MagicMock()
        row.lat = 99.0
        row.lon = 99.0

        async def _mock_execute(*a, **kw):
            r = MagicMock()
            r.scalar_one_or_none.return_value = row
            return r

        db.execute.side_effect = _mock_execute
        result = await get_city_center("testville", db=db)
        assert result == (99.0, 99.0)
