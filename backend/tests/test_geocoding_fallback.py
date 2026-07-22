# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import pytest

from core.config import Settings
from services.geocoding_service import GeocodingService


class FakePhotonClient:
    def __init__(self, *, should_fail=False):
        self.should_fail = should_fail

    async def reverse(self, *, lat, lon):
        if self.should_fail:
            raise RuntimeError("Photon API unavailable")
        return {
            "display_name": "Photon City, Photon State",
            "city": "Photon City",
            "state": "Photon State",
            "country": "India",
        }

    async def search(self, *, query, limit=5):
        if self.should_fail:
            raise RuntimeError("Photon API unavailable")
        return [
            {"display_name": "Photon Result, City", "lat": 13.08, "lon": 80.27},
        ]


class FakeNominatimClient:
    def __init__(self, *, should_fail=False):
        self.should_fail = should_fail

    async def reverse(self, *, lat, lon):
        if self.should_fail:
            raise RuntimeError("Nominatim API unavailable")
        return {
            "display_name": "Nominatim City, Nominatim State",
            "city": "Nominatim City",
            "state": "Nominatim State",
            "country": "India",
        }

    async def search(self, *, query, limit=5):
        if self.should_fail:
            raise RuntimeError("Nominatim API unavailable")
        return [
            {"display_name": "Nominatim Result, City", "lat": 13.08, "lon": 80.27},
        ]


class FakeBigDataClient:
    def __init__(self, *, should_fail=False):
        self.should_fail = should_fail

    async def reverse(self, *, lat, lon):
        if self.should_fail:
            raise RuntimeError("BigData API unavailable")
        return {
            "display_name": "BigData City, BigData State",
            "city": "BigData City",
            "state": "BigData State",
            "country": "IN",
        }


class TestPhotonPrimary:
    def test_photon_used_first(self):
        photon = FakePhotonClient(should_fail=False)
        nominatim = FakeNominatimClient(should_fail=False)
        bigdata = FakeBigDataClient(should_fail=False)

        service = GeocodingService(
            Settings(),
            photon_client=photon,
            nominatim_client=nominatim,
            bigdata_client=bigdata,
        )

        import asyncio

        result = asyncio.run(service.reverse_geocode(lat=13.0827, lon=80.2707))

        assert "Photon" in result["display_name"]


class TestNominatimFallback:
    def test_nominatim_used_when_photon_fails(self):
        photon = FakePhotonClient(should_fail=True)
        nominatim = FakeNominatimClient(should_fail=False)
        bigdata = FakeBigDataClient(should_fail=False)

        service = GeocodingService(
            Settings(),
            photon_client=photon,
            nominatim_client=nominatim,
            bigdata_client=bigdata,
        )

        import asyncio

        result = asyncio.run(service.reverse_geocode(lat=13.0827, lon=80.2707))

        assert "Nominatim" in result["display_name"]


class TestBigDataFallback:
    def test_bigdata_used_when_photon_and_nominatim_fail(self):
        photon = FakePhotonClient(should_fail=True)
        nominatim = FakeNominatimClient(should_fail=True)
        bigdata = FakeBigDataClient(should_fail=False)

        service = GeocodingService(
            Settings(),
            photon_client=photon,
            nominatim_client=nominatim,
            bigdata_client=bigdata,
        )

        import asyncio

        result = asyncio.run(service.reverse_geocode(lat=13.0827, lon=80.2707))

        assert "BigData" in result["display_name"]


class TestAllFailGraceful:
    def test_all_providers_fail_gracefully(self):
        photon = FakePhotonClient(should_fail=True)
        nominatim = FakeNominatimClient(should_fail=True)
        bigdata = FakeBigDataClient(should_fail=True)

        service = GeocodingService(
            Settings(),
            photon_client=photon,
            nominatim_client=nominatim,
            bigdata_client=bigdata,
        )

        import asyncio

        with pytest.raises(Exception):
            asyncio.run(service.reverse_geocode(lat=13.0827, lon=80.2707))
