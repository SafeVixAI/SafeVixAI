# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path
from urllib.parse import quote_plus

import httpx

from core.circuit_breaker import CircuitBreakerOpenError, CircuitBreakerRegistry
from core.config import Settings
from core.redis_client import CacheHelper
from models.schemas import GeocodeResult
from services.exceptions import ExternalServiceError

# alert_service.py at project root
for parent in Path(__file__).resolve().parents:
    if (parent / 'alert_service.py').exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break
from core.alert import get_alert_service  # noqa: E402

logger = logging.getLogger("safevixai.backend.geocoding")


class GeocodingError(ExternalServiceError):
    pass


class GeocodingService:
    def __init__(
        self,
        settings: Settings,
        cache: CacheHelper | None = None,
        photon_client=None,
        nominatim_client=None,
        bigdata_client=None,
    ) -> None:
        self.settings = settings
        self.cache = cache
        self._client = httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            headers={'User-Agent': settings.http_user_agent},
        )
        self._rate_limit_lock = asyncio.Lock()
        self._last_nominatim_request_at = 0.0
        self.photon_client = photon_client
        self.nominatim_client = nominatim_client
        self.bigdata_client = bigdata_client

    async def aclose(self) -> None:
        await self._client.aclose()

    async def reverse_geocode(self, *, lat: float, lon: float) -> dict:
        errors = []
        if self.photon_client:
            try:
                return await self.photon_client.reverse(lat=lat, lon=lon)
            except Exception as e:
                logger.warning("Photon reverse geocode failed: %s", e, extra={"service": "geocoding"})
                errors.append(e)
        if self.nominatim_client:
            try:
                return await self.nominatim_client.reverse(lat=lat, lon=lon)
            except Exception as e:
                logger.warning("Nominatim reverse geocode failed: %s", e, extra={"service": "geocoding"})
                errors.append(e)
        if self.bigdata_client:
            try:
                return await self.bigdata_client.reverse(lat=lat, lon=lon)
            except Exception as e:
                logger.warning("BigDataCloud reverse geocode failed: %s", e, extra={"service": "geocoding"})
                errors.append(e)
        msg = f"All providers failed: {errors}"
        raise GeocodingError(msg)

    async def reverse(self, *, lat: float, lon: float) -> GeocodeResult:
        if self.cache is None:
            res_dict = await self.reverse_geocode(lat=lat, lon=lon)
            return GeocodeResult(
                display_name=res_dict.get("display_name", "Unknown location"),
                city=res_dict.get("city"),
                state=res_dict.get("state"),
                country_code=res_dict.get("country"),
                postcode=res_dict.get("postcode"),
                lat=lat,
                lon=lon,
            )

        cache_key = f'geocode:reverse:{lat:.4f}:{lon:.4f}'
        cached = await self.cache.get_json(cache_key)
        if cached:
            return GeocodeResult.model_validate(cached)

        try:
            result = await self._reverse_photon(lat=lat, lon=lon)
        except GeocodingError:
            try:
                result = await self._reverse_nominatim(lat=lat, lon=lon)
            except GeocodingError:
                get_alert_service().alert_external_api_failed(
                    service_name="Geocoding (Photon + Nominatim)",
                    endpoint=f"reverse lat={lat} lon={lon}",
                    status_code=0,
                    error_msg="Both Photon and Nominatim failed for reverse geocoding",
                )
                raise

        await self.cache.set_json(cache_key, result.model_dump(mode='json'), self.settings.geocode_cache_ttl_seconds)
        return result

    async def search(self, query: str) -> list[GeocodeResult]:
        cache_key = f'geocode:search:{quote_plus(query.lower())}'
        cached = await self.cache.get_json(cache_key)
        if cached:
            return [GeocodeResult.model_validate(item) for item in cached]

        try:
            results = await self._search_photon(query)
        except GeocodingError:
            try:
                results = await self._search_nominatim(query)
            except GeocodingError:
                get_alert_service().alert_external_api_failed(
                    service_name="Geocoding (Photon + Nominatim)",
                    endpoint=f"search q={query[:50]}",
                    status_code=0,
                    error_msg="Both Photon and Nominatim failed for forward geocoding",
                )
                raise

        await self.cache.set_json(
            cache_key,
            [result.model_dump(mode='json') for result in results],
            self.settings.geocode_cache_ttl_seconds,
        )
        return results

    async def _search_photon(self, query: str) -> list[GeocodeResult]:
        payload = await self._get(self.settings.photon_url, '/api/', {'q': query, 'limit': 5, 'lang': 'en'})
        features = payload.get('features') if isinstance(payload, dict) else None
        if not features:
            msg = 'Photon geocoding unavailable'
            raise GeocodingError(msg)
        return [self._normalize_photon(feature) for feature in features if feature]

    async def _reverse_photon(self, *, lat: float, lon: float) -> GeocodeResult:
        payload = await self._get(self.settings.photon_url, '/reverse', {'lat': lat, 'lon': lon, 'limit': 1})
        features = payload.get('features') if isinstance(payload, dict) else None
        if not features:
            msg = 'Photon geocoding unavailable'
            raise GeocodingError(msg)
        return self._normalize_photon(features[0])

    async def _search_nominatim(self, query: str) -> list[GeocodeResult]:
        params = {
            'q': query,
            'format': 'jsonv2',
            'addressdetails': 1,
            'limit': 5,
        }
        payload = await self._get_nominatim('/search', params)
        return [self._normalize_nominatim(item) for item in payload]

    async def _reverse_nominatim(self, *, lat: float, lon: float) -> GeocodeResult:
        params = {
            'lat': lat,
            'lon': lon,
            'format': 'jsonv2',
            'addressdetails': 1,
        }
        payload = await self._get_nominatim('/reverse', params)
        return self._normalize_nominatim(payload)

    async def _get_nominatim(self, path: str, params: dict) -> dict | list:
        cb = CircuitBreakerRegistry.get("nominatim", failure_threshold=3, recovery_timeout=60.0)
        try:
            return await cb.call(self._do_get_nominatim, path, params)
        except CircuitBreakerOpenError:
            logger.warning("Nominatim circuit breaker OPEN")
            msg = "Nominatim unavailable (circuit breaker open)"
            raise GeocodingError(msg)

    async def _do_get_nominatim(self, path: str, params: dict) -> dict | list:
        async with self._rate_limit_lock:
            elapsed = time.monotonic() - self._last_nominatim_request_at
            if elapsed < 1.0:
                await asyncio.sleep(1.0 - elapsed)
            try:
                response = await self._client.get(f'{self.settings.nominatim_url}{path}', params=params)
                response.raise_for_status()
            except httpx.HTTPError as exc:
                msg = 'Nominatim geocoding unavailable'
                raise GeocodingError(msg) from exc
            finally:
                self._last_nominatim_request_at = time.monotonic()
        return response.json()

    async def _get(self, base_url: str, path: str, params: dict) -> dict | list:
        cb = CircuitBreakerRegistry.get("photon", failure_threshold=3, recovery_timeout=30.0)
        try:
            return await cb.call(self._do_get, base_url, path, params)
        except CircuitBreakerOpenError:
            logger.warning("Photon circuit breaker OPEN")
            msg = "Photon unavailable (circuit breaker open)"
            raise GeocodingError(msg)

    async def _do_get(self, base_url: str, path: str, params: dict) -> dict | list:
        try:
            response = await self._client.get(f'{base_url}{path}', params=params)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            msg = 'Photon geocoding unavailable'
            raise GeocodingError(msg) from exc
        return response.json()

    @staticmethod
    def _normalize_photon(feature: dict) -> GeocodeResult:
        properties = feature.get('properties', {})
        geometry = feature.get('geometry', {})
        coordinates = geometry.get('coordinates') or [None, None]
        lon = float(coordinates[0]) if coordinates[0] is not None else None
        lat = float(coordinates[1]) if coordinates[1] is not None else None

        city = (
            properties.get('city')
            or properties.get('district')
            or properties.get('county')
            or properties.get('state_district')
            or properties.get('locality')
        )
        state_code = properties.get('statecode') or properties.get('state_code')
        country_code = (properties.get('countrycode') or '').upper() or None
        name = properties.get('name')
        street = ' '.join(part for part in [properties.get('street'), properties.get('housenumber')] if part)
        display_parts = [name, street or None, city, properties.get('state'), properties.get('country')]
        display_name = ', '.join(part for part in display_parts if part) or 'Unknown location'

        return GeocodeResult(
            display_name=display_name,
            city=city,
            state=properties.get('state'),
            state_code=state_code,
            country_code=country_code,
            postcode=properties.get('postcode'),
            lat=lat,
            lon=lon,
        )

    @staticmethod
    def _normalize_nominatim(payload: dict) -> GeocodeResult:
        address = payload.get('address', {})
        state_code = address.get('ISO3166-2-lvl4')
        if state_code and '-' in state_code:
            state_code = state_code.split('-')[-1]
        return GeocodeResult(
            display_name=payload.get('display_name', 'Unknown location'),
            city=address.get('city') or address.get('town') or address.get('village') or address.get('county'),
            state=address.get('state'),
            state_code=state_code,
            country_code=(address.get('country_code') or '').upper() or None,
            postcode=address.get('postcode'),
            lat=float(payload['lat']) if payload.get('lat') is not None else None,
            lon=float(payload['lon']) if payload.get('lon') is not None else None,
        )
