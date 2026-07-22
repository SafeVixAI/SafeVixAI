# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.config import Settings
from core.redis_client import CacheHelper
from models.schemas import GeocodeResult
from services.geocoding_service import GeocodingError, GeocodingService

# ── Fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def settings():
    return Settings()


@pytest.fixture
def cache():
    return AsyncMock(spec=CacheHelper)


@pytest.fixture
def photon_client():
    return AsyncMock()


@pytest.fixture
def nominatim_client():
    return AsyncMock()


@pytest.fixture
def bigdata_client():
    return AsyncMock()


@pytest.fixture
def service(settings, cache):
    with patch('services.geocoding_service.httpx.AsyncClient'):
        svc = GeocodingService(settings=settings, cache=cache)
        yield svc


# ── 1. Constructor ──────────────────────────────────────────────────────

class TestConstructor:
    def test_creates_http_client_with_correct_settings(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient') as mock_client_cls:
            svc = GeocodingService(settings=settings)
            mock_client_cls.assert_called_once_with(
                timeout=settings.request_timeout_seconds,
                headers={'User-Agent': settings.http_user_agent},
            )
            assert svc.settings == settings
            assert svc.cache is None
            assert svc.photon_client is None
            assert svc.nominatim_client is None
            assert svc.bigdata_client is None
            assert svc._last_nominatim_request_at == 0.0
            assert svc._rate_limit_lock is not None

    def test_accepts_custom_clients(self, settings):
        pc = AsyncMock()
        nc = AsyncMock()
        bc = AsyncMock()
        ca = AsyncMock()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(
                settings=settings, cache=ca,
                photon_client=pc, nominatim_client=nc, bigdata_client=bc,
            )
            assert svc.photon_client is pc
            assert svc.nominatim_client is nc
            assert svc.bigdata_client is bc
            assert svc.cache is ca

    def test_lock_and_timer_initialized(self, settings):
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc1 = GeocodingService(settings=settings)
            svc2 = GeocodingService(settings=settings)
            assert svc1._last_nominatim_request_at == 0.0
            assert svc1._rate_limit_lock is not None
            assert type(svc1._rate_limit_lock) is type(svc2._rate_limit_lock)


# ── 2. aclose ──────────────────────────────────────────────────────────

class TestAclose:
    async def test_acloses_http_client(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            svc._client.aclose = AsyncMock()
            await svc.aclose()
            svc._client.aclose.assert_awaited_once()


# ── 3-6. reverse_geocode ──────────────────────────────────────────────

class TestReverseGeocode:
    async def test_photon_success_returns_result(self, settings, photon_client):
        expected = {"display_name": "Chennai", "city": "Chennai", "state": "Tamil Nadu"}
        photon_client.reverse.return_value = expected
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(
                settings=settings, photon_client=photon_client,
                nominatim_client=None, bigdata_client=None,
            )
            result = await svc.reverse_geocode(lat=13.0, lon=80.0)
            assert result == expected
            photon_client.reverse.assert_awaited_once_with(lat=13.0, lon=80.0)

    async def test_photon_fails_nominatim_succeeds(self, settings, photon_client, nominatim_client):
        expected = {"display_name": "Delhi", "city": "Delhi"}
        photon_client.reverse.side_effect = Exception("Photon down")
        nominatim_client.reverse.return_value = expected
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(
                settings=settings, photon_client=photon_client,
                nominatim_client=nominatim_client, bigdata_client=None,
            )
            result = await svc.reverse_geocode(lat=28.0, lon=77.0)
            assert result == expected
            photon_client.reverse.assert_awaited_once_with(lat=28.0, lon=77.0)
            nominatim_client.reverse.assert_awaited_once_with(lat=28.0, lon=77.0)

    async def test_all_providers_fail_raises_error(
        self, settings, photon_client, nominatim_client, bigdata_client,
    ):
        photon_client.reverse.side_effect = Exception("Photon down")
        nominatim_client.reverse.side_effect = Exception("Nominatim down")
        bigdata_client.reverse.side_effect = Exception("BigDataCloud down")
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(
                settings=settings, photon_client=photon_client,
                nominatim_client=nominatim_client, bigdata_client=bigdata_client,
            )
            with pytest.raises(GeocodingError, match="All providers failed"):
                await svc.reverse_geocode(lat=0.0, lon=0.0)

    async def test_only_bigdatacloud_works(
        self, settings, photon_client, nominatim_client, bigdata_client,
    ):
        photon_client.reverse.side_effect = Exception("Photon down")
        nominatim_client.reverse.side_effect = Exception("Nominatim down")
        expected = {"display_name": "Mumbai", "city": "Mumbai"}
        bigdata_client.reverse.return_value = expected
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(
                settings=settings, photon_client=photon_client,
                nominatim_client=nominatim_client, bigdata_client=bigdata_client,
            )
            result = await svc.reverse_geocode(lat=19.0, lon=72.0)
            assert result == expected
            bigdata_client.reverse.assert_awaited_once_with(lat=19.0, lon=72.0)

    async def test_photon_none_then_nominatim_skipped_then_bigdata(
        self, settings, photon_client, bigdata_client,
    ):
        photon_client.reverse.side_effect = Exception("Photon down")
        expected = {"display_name": "Bangalore"}
        bigdata_client.reverse.return_value = expected
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(
                settings=settings, photon_client=photon_client,
                nominatim_client=None, bigdata_client=bigdata_client,
            )
            result = await svc.reverse_geocode(lat=12.0, lon=77.0)
            assert result == expected

    async def test_photon_return_value_is_returned_directly(self, settings, photon_client):
        photon_client.reverse.return_value = None
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(
                settings=settings, photon_client=photon_client,
                nominatim_client=None, bigdata_client=None,
            )
            result = await svc.reverse_geocode(lat=13.0, lon=80.0)
            assert result is None


# ── 7-10. reverse ─────────────────────────────────────────────────────

class TestReverse:
    async def test_cached_hit_returns_from_cache(self, service, cache):
        cached_result = GeocodeResult(
            display_name="Cached City", city="Cached", lat=13.0, lon=80.0,
        )
        cache.get_json.return_value = cached_result.model_dump(mode='json')
        result = await service.reverse(lat=13.0, lon=80.0)
        assert result == cached_result
        cache.get_json.assert_awaited_once_with("geocode:reverse:13.0000:80.0000")

    async def test_cache_miss_photon_success_caches_result(self, service, cache):
        cache.get_json.return_value = None
        expected = GeocodeResult(
            display_name="Photon City", city="Photon", lat=13.0, lon=80.0,
        )
        with patch.object(GeocodingService, '_reverse_photon', new_callable=AsyncMock) as mock_rev:
            mock_rev.return_value = expected
            result = await service.reverse(lat=13.0, lon=80.0)
            assert result == expected
            cache.set_json.assert_awaited_once_with(
                "geocode:reverse:13.0000:80.0000",
                expected.model_dump(mode='json'),
                service.settings.geocode_cache_ttl_seconds,
            )

    async def test_photon_fails_nominatim_succeeds(self, service, cache):
        cache.get_json.return_value = None
        expected = GeocodeResult(
            display_name="Nominatim City", city="Nominatim", lat=13.0, lon=80.0,
        )
        with (
            patch.object(GeocodingService, '_reverse_photon', new_callable=AsyncMock) as mock_photon,
            patch.object(GeocodingService, '_reverse_nominatim', new_callable=AsyncMock) as mock_nom,
        ):
            mock_photon.side_effect = GeocodingError("Photon unavailable")
            mock_nom.return_value = expected
            result = await service.reverse(lat=13.0, lon=80.0)
            assert result == expected
            mock_photon.assert_awaited_once_with(lat=13.0, lon=80.0)
            mock_nom.assert_awaited_once_with(lat=13.0, lon=80.0)

    async def test_both_fail_alert_and_raise(self, service, cache):
        cache.get_json.return_value = None
        with (
            patch.object(GeocodingService, '_reverse_photon', new_callable=AsyncMock) as mock_photon,
            patch.object(GeocodingService, '_reverse_nominatim', new_callable=AsyncMock) as mock_nom,
            patch('services.geocoding_service.get_alert_service') as mock_alerts,
        ):
            mock_photon.side_effect = GeocodingError("Photon unavailable")
            mock_nom.side_effect = GeocodingError("Nominatim unavailable")
            mock_alert_svc = MagicMock()
            mock_alerts.return_value = mock_alert_svc
            with pytest.raises(GeocodingError):
                await service.reverse(lat=13.0, lon=80.0)
            mock_alert_svc.alert_external_api_failed.assert_called_once_with(
                service_name="Geocoding (Photon + Nominatim)",
                endpoint="reverse lat=13.0 lon=80.0",
                status_code=0,
                error_msg="Both Photon and Nominatim failed for reverse geocoding",
            )

    async def test_without_cache_calls_reverse_geocode_and_builds_result(self, settings):
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings, cache=None)
            svc.nominatim_client = AsyncMock()
            expected_nominatim = {
                "display_name": "Direct City", "city": "Direct",
                "state": "State", "country": "IN", "postcode": "123",
            }
            svc.nominatim_client.reverse.return_value = expected_nominatim
            svc.nominatim_client.reverse.return_value = expected_nominatim
            result = await svc.reverse(lat=13.0, lon=80.0)
            assert result.display_name == "Direct City"
            assert result.city == "Direct"
            assert result.state == "State"
            assert result.country_code == "IN"
            assert result.postcode == "123"
            assert result.lat == 13.0
            assert result.lon == 80.0


# ── 11-14. search ────────────────────────────────────────────────────

class TestSearch:
    async def test_cached_hit_returns_list_from_cache(self, service, cache):
        cached = [
            GeocodeResult(display_name="Place A", lat=1.0, lon=1.0).model_dump(mode='json'),
            GeocodeResult(display_name="Place B", lat=2.0, lon=2.0).model_dump(mode='json'),
        ]
        cache.get_json.return_value = cached
        results = await service.search("test query")
        assert len(results) == 2
        assert results[0].display_name == "Place A"
        assert results[1].display_name == "Place B"

    async def test_photon_success_caches_results(self, service, cache):
        cache.get_json.return_value = None
        expected = [
            GeocodeResult(display_name="Result A", lat=1.0, lon=1.0),
            GeocodeResult(display_name="Result B", lat=2.0, lon=2.0),
        ]
        with patch.object(GeocodingService, '_search_photon', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = expected
            results = await service.search("main road")
            assert results == expected
            cache.set_json.assert_awaited_once()

    async def test_photon_fails_nominatim_succeeds(self, service, cache):
        cache.get_json.return_value = None
        expected = [GeocodeResult(display_name="Nom Result", lat=3.0, lon=3.0)]
        with (
            patch.object(GeocodingService, '_search_photon', new_callable=AsyncMock) as mock_photon,
            patch.object(GeocodingService, '_search_nominatim', new_callable=AsyncMock) as mock_nom,
        ):
            mock_photon.side_effect = GeocodingError("Photon unavailable")
            mock_nom.return_value = expected
            results = await service.search("park street")
            assert results == expected
            mock_photon.assert_awaited_once_with("park street")
            mock_nom.assert_awaited_once_with("park street")

    async def test_both_fail_alert_and_raise(self, service, cache):
        cache.get_json.return_value = None
        with (
            patch.object(GeocodingService, '_search_photon', new_callable=AsyncMock) as mock_photon,
            patch.object(GeocodingService, '_search_nominatim', new_callable=AsyncMock) as mock_nom,
            patch('services.geocoding_service.get_alert_service') as mock_alerts,
        ):
            mock_photon.side_effect = GeocodingError("Photon unavailable")
            mock_nom.side_effect = GeocodingError("Nominatim unavailable")
            mock_alert_svc = MagicMock()
            mock_alerts.return_value = mock_alert_svc
            with pytest.raises(GeocodingError):
                await service.search("unknown place")
            mock_alert_svc.alert_external_api_failed.assert_called_once_with(
                service_name="Geocoding (Photon + Nominatim)",
                endpoint="search q=unknown place",
                status_code=0,
                error_msg="Both Photon and Nominatim failed for forward geocoding",
            )


# ── 15-17. _normalize_photon ────────────────────────────────────────────

class TestNormalizePhoton:
    def test_full_address_parsed_correctly(self):
        feature = {
            "geometry": {"coordinates": [80.2707, 13.0827]},
            "properties": {
                "name": "Marina Beach",
                "street": "Marina Beach Road",
                "housenumber": "1",
                "city": "Chennai",
                "state": "Tamil Nadu",
                "statecode": "TN",
                "country": "India",
                "countrycode": "IN",
                "postcode": "600001",
            },
        }
        result = GeocodingService._normalize_photon(feature)
        assert result.display_name == "Marina Beach, Marina Beach Road 1, Chennai, Tamil Nadu, India"
        assert result.city == "Chennai"
        assert result.state == "Tamil Nadu"
        assert result.state_code == "TN"
        assert result.country_code == "IN"
        assert result.postcode == "600001"
        assert result.lat == 13.0827
        assert result.lon == 80.2707

    def test_minimal_fields_only_name(self):
        feature = {
            "geometry": {"coordinates": [None, None]},
            "properties": {"name": "Some Place"},
        }
        result = GeocodingService._normalize_photon(feature)
        assert result.display_name == "Some Place"
        assert result.city is None
        assert result.state is None
        assert result.state_code is None
        assert result.country_code is None
        assert result.postcode is None
        assert result.lat is None
        assert result.lon is None

    def test_missing_coordinates(self):
        feature = {
            "geometry": {},
            "properties": {"name": "No Coords"},
        }
        result = GeocodingService._normalize_photon(feature)
        assert result.display_name == "No Coords"
        assert result.lat is None
        assert result.lon is None

    def test_empty_properties_uses_unknown_fallback(self):
        feature = {"geometry": {"coordinates": [0, 0]}, "properties": {}}
        result = GeocodingService._normalize_photon(feature)
        assert result.display_name == "Unknown location"
        assert result.lat == 0.0
        assert result.lon == 0.0

    def test_countrycode_uppercased(self):
        feature = {
            "geometry": {"coordinates": [0, 0]},
            "properties": {"name": "X", "countrycode": "in"},
        }
        result = GeocodingService._normalize_photon(feature)
        assert result.country_code == "IN"

    def test_city_fallback_chain_county_before_locality(self):
        feature = {
            "geometry": {"coordinates": [0, 0]},
            "properties": {"name": "X", "locality": "MyLocality", "county": "MyCounty"},
        }
        result = GeocodingService._normalize_photon(feature)
        assert result.city == "MyCounty"

    def test_city_uses_district_when_city_missing(self):
        feature = {
            "geometry": {"coordinates": [0, 0]},
            "properties": {"name": "X", "district": "MyDistrict"},
        }
        result = GeocodingService._normalize_photon(feature)
        assert result.city == "MyDistrict"


# ── 18-20. _normalize_nominatim ─────────────────────────────────────────

class TestNormalizeNominatim:
    def test_full_address_parsed_correctly(self):
        payload = {
            "display_name": "Taj Mahal, Agra, Uttar Pradesh, India",
            "lat": "27.1751",
            "lon": "78.0421",
            "address": {
                "city": "Agra",
                "state": "Uttar Pradesh",
                "ISO3166-2-lvl4": "IN-UP",
                "country_code": "in",
                "postcode": "282001",
            },
        }
        result = GeocodingService._normalize_nominatim(payload)
        assert result.display_name == "Taj Mahal, Agra, Uttar Pradesh, India"
        assert result.city == "Agra"
        assert result.state == "Uttar Pradesh"
        assert result.state_code == "UP"
        assert result.country_code == "IN"
        assert result.postcode == "282001"
        assert result.lat == 27.1751
        assert result.lon == 78.0421

    def test_minimal_fields(self):
        payload = {"display_name": "Unknown", "address": {}}
        result = GeocodingService._normalize_nominatim(payload)
        assert result.display_name == "Unknown"
        assert result.city is None
        assert result.state is None
        assert result.state_code is None
        assert result.country_code is None
        assert result.postcode is None
        assert result.lat is None
        assert result.lon is None

    def test_state_code_with_iso3166_format(self):
        payload = {
            "display_name": "Test",
            "address": {"ISO3166-2-lvl4": "US-CA"},
        }
        result = GeocodingService._normalize_nominatim(payload)
        assert result.state_code == "CA"

    def test_state_code_without_dash_unchanged(self):
        payload = {
            "display_name": "Test",
            "address": {"ISO3166-2-lvl4": "KA"},
        }
        result = GeocodingService._normalize_nominatim(payload)
        assert result.state_code == "KA"

    def test_country_code_uppercased(self):
        payload = {
            "display_name": "Test",
            "address": {"country_code": "gb"},
        }
        result = GeocodingService._normalize_nominatim(payload)
        assert result.country_code == "GB"

    def test_city_fallback_chain(self):
        payload = {
            "display_name": "Test",
            "address": {"town": "MyTown", "county": "MyCounty"},
        }
        result = GeocodingService._normalize_nominatim(payload)
        assert result.city == "MyTown"

    def test_city_uses_village_when_no_city_or_town(self):
        payload = {
            "display_name": "Test",
            "address": {"village": "MyVillage", "county": "MyCounty"},
        }
        result = GeocodingService._normalize_nominatim(payload)
        assert result.city == "MyVillage"


# ── 21-22. _get ───────────────────────────────────────────────────────

class TestGet:
    async def _make_service_and_mock_get(self, settings):
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_response = MagicMock()
            mock_response.json.return_value = {"features": [{"id": "1"}]}
            mock_response.raise_for_status.return_value = None
            svc._client = MagicMock()
            async def fake_get(*args, **kwargs):
                return mock_response
            svc._client.get = fake_get
            return svc, mock_response

    async def test_success_returns_json(self):
        settings = Settings()
        MagicMock()  # We only need _get, so stub the whole service
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": [{"id": "1"}]}
        mock_response.raise_for_status.return_value = None
        mock_client = MagicMock()
        async def fake_get(*args, **kwargs):
            return mock_response
        mock_client.get = fake_get

        with patch('services.geocoding_service.httpx.AsyncClient'):
            real_svc = GeocodingService(settings=settings)
            real_svc._client = mock_client
            result = await real_svc._get("https://photon.komoot.io", "/api", {"q": "test"})
            assert result == {"features": [{"id": "1"}]}

    async def test_http_error_raises_geocoding_error(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_client = MagicMock()
            async def fake_get(*args, **kwargs):
                raise httpx.HTTPError("connection failed")
            mock_client.get = fake_get
            svc._client = mock_client
            with pytest.raises(GeocodingError, match="Photon geocoding unavailable"):
                await svc._get("https://photon.komoot.io", "/api", {"q": "test"})

    async def test_timeout_raises_geocoding_error(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_client = MagicMock()
            async def fake_get(*args, **kwargs):
                raise httpx.TimeoutException("timed out")
            mock_client.get = fake_get
            svc._client = mock_client
            with pytest.raises(GeocodingError, match="Photon geocoding unavailable"):
                await svc._get("https://photon.komoot.io", "/api", {"q": "test"})


# ── 23-25. _get_nominatim ─────────────────────────────────────────────

class TestGetNominatim:
    async def test_success_respects_rate_limit_first_call(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            assert svc._last_nominatim_request_at == 0.0
            mock_response = MagicMock()
            mock_response.json.return_value = {"display_name": "Test Place"}
            mock_response.raise_for_status.return_value = None
            mock_client = MagicMock()
            async def fake_get(*args, **kwargs):
                return mock_response
            mock_client.get = fake_get
            svc._client = mock_client
            result = await svc._get_nominatim("/reverse", {"lat": 1, "lon": 2})
            assert result == {"display_name": "Test Place"}
            assert svc._last_nominatim_request_at > 0

    async def test_rate_limited_waits_between_requests(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            svc._last_nominatim_request_at = time.monotonic() - 0.3
            mock_response = MagicMock()
            mock_response.json.return_value = {"display_name": "Test"}
            mock_response.raise_for_status.return_value = None
            mock_client = MagicMock()
            async def fake_get(*args, **kwargs):
                return mock_response
            mock_client.get = fake_get
            svc._client = mock_client
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await svc._get_nominatim("/search", {"q": "test"})
                assert result == {"display_name": "Test"}
                mock_sleep.assert_awaited_once()
                sleep_arg = mock_sleep.call_args[0][0]
                assert 0.6 <= sleep_arg <= 0.8

    async def test_no_sleep_when_sufficient_time_elapsed(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            svc._last_nominatim_request_at = time.monotonic() - 5.0
            mock_response = MagicMock()
            mock_response.json.return_value = {"display_name": "Test"}
            mock_response.raise_for_status.return_value = None
            mock_client = MagicMock()
            async def fake_get(*args, **kwargs):
                return mock_response
            mock_client.get = fake_get
            svc._client = mock_client
            with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
                result = await svc._get_nominatim("/reverse", {"lat": 1, "lon": 2})
                assert result == {"display_name": "Test"}
                mock_sleep.assert_not_called()

    async def test_http_error_raises_geocoding_error(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_client = MagicMock()
            async def fake_get(*args, **kwargs):
                raise httpx.HTTPError("Nominatim down")
            mock_client.get = fake_get
            svc._client = mock_client
            with pytest.raises(GeocodingError, match="Nominatim geocoding unavailable"):
                await svc._get_nominatim("/reverse", {"lat": 1, "lon": 2})

    async def test_http_status_error_raises_geocoding_error(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_client = MagicMock()
            async def fake_get(*args, **kwargs):
                raise httpx.HTTPStatusError(
                    "429 Too Many Requests", request=MagicMock(), response=MagicMock(),
                )
            mock_client.get = fake_get
            svc._client = mock_client
            with pytest.raises(GeocodingError, match="Nominatim geocoding unavailable"):
                await svc._get_nominatim("/search", {"q": "test"})


# ── 26-29. _search_photon / _reverse_photon / _search_nominatim / _reverse_nominatim ──


class TestSearchPhoton:
    async def test_returns_results(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "features": [
                    {"geometry": {"coordinates": [80.27, 13.08]}, "properties": {"name": "Test Place", "city": "Chennai"}},
                ]
            }
            mock_resp.raise_for_status.return_value = None
            svc._client = MagicMock()
            async def fake_get(*args, **kwargs):
                return mock_resp
            svc._client.get = fake_get
            results = await svc._search_photon("chennai")
            assert len(results) == 1
            assert results[0].city == "Chennai"

    async def test_no_features_raises(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_resp = MagicMock()
            mock_resp.json.return_value = {}
            mock_resp.raise_for_status.return_value = None
            svc._client = MagicMock()
            async def fake_get(*args, **kwargs):
                return mock_resp
            svc._client.get = fake_get
            with pytest.raises(GeocodingError, match="Photon geocoding unavailable"):
                await svc._search_photon("nowhere")


class TestReversePhoton:
    async def test_returns_result(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "features": [
                    {"geometry": {"coordinates": [80.27, 13.08]}, "properties": {"name": "Place", "city": "Chennai"}},
                ]
            }
            mock_resp.raise_for_status.return_value = None
            svc._client = MagicMock()
            async def fake_get(*args, **kwargs):
                return mock_resp
            svc._client.get = fake_get
            result = await svc._reverse_photon(lat=13.08, lon=80.27)
            assert result.city == "Chennai"

    async def test_no_features_raises(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_resp = MagicMock()
            mock_resp.json.return_value = {}
            mock_resp.raise_for_status.return_value = None
            svc._client = MagicMock()
            async def fake_get(*args, **kwargs):
                return mock_resp
            svc._client.get = fake_get
            with pytest.raises(GeocodingError, match="Photon geocoding unavailable"):
                await svc._reverse_photon(lat=0.0, lon=0.0)


class TestSearchNominatim:
    async def test_returns_results(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_resp = MagicMock()
            mock_resp.json.return_value = [
                {"display_name": "Chennai, India", "lat": "13.08", "lon": "80.27", "address": {"city": "Chennai"}},
            ]
            mock_resp.raise_for_status.return_value = None
            svc._client = MagicMock()
            async def fake_get(*args, **kwargs):
                mock_resp.raise_for_status.return_value = None
                return mock_resp
            svc._client.get = fake_get
            with patch.object(svc, '_last_nominatim_request_at', 0.0), patch('asyncio.sleep', new_callable=AsyncMock):
                results = await svc._search_nominatim("chennai")
            assert len(results) == 1
            assert results[0].city == "Chennai"

    async def test_empty_response(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_resp = MagicMock()
            mock_resp.json.return_value = []
            mock_resp.raise_for_status.return_value = None
            svc._client = MagicMock()
            async def fake_get(*args, **kwargs):
                mock_resp.raise_for_status.return_value = None
                return mock_resp
            svc._client.get = fake_get
            with patch.object(svc, '_last_nominatim_request_at', 0.0), patch('asyncio.sleep', new_callable=AsyncMock):
                results = await svc._search_nominatim("")
            assert results == []


class TestReverseNominatim:
    async def test_returns_result(self):
        settings = Settings()
        with patch('services.geocoding_service.httpx.AsyncClient'):
            svc = GeocodingService(settings=settings)
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "display_name": "Test, Chennai, India",
                "lat": "13.08", "lon": "80.27",
                "address": {"city": "Chennai", "state": "Tamil Nadu", "country_code": "in", "postcode": "600001"},
            }
            mock_resp.raise_for_status.return_value = None
            svc._client = MagicMock()
            async def fake_get(*args, **kwargs):
                mock_resp.raise_for_status.return_value = None
                return mock_resp
            svc._client.get = fake_get
            with patch.object(svc, '_last_nominatim_request_at', 0.0), patch('asyncio.sleep', new_callable=AsyncMock):
                result = await svc._reverse_nominatim(lat=13.08, lon=80.27)
            assert result.city == "Chennai"
            assert result.state == "Tamil Nadu"
            assert result.country_code == "IN"
