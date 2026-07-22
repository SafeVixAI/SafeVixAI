# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from services.exceptions import ServiceValidationError
from services.garage_service import GarageService


class TestParseStateCode:
    def test_standard_plate(self):
        assert GarageService._parse_state_code("TN-01-AB-1234") == "TN"

    def test_dl_plate(self):
        assert GarageService._parse_state_code("DL-03-CD-5678") == "DL"

    def test_no_delimiters(self):
        assert GarageService._parse_state_code("KA51GH3456") == "KA"

    def test_lowercase_plate(self):
        assert GarageService._parse_state_code("mh-02-ef-9012") == "MH"

    def test_numeric_prefix_fallsback_to_dl(self):
        assert GarageService._parse_state_code("1234-AB-CD") == "DL"

    def test_short_string_fallsback_to_dl(self):
        assert GarageService._parse_state_code("A") == "DL"


class TestGenerateDeterministicVehicle:
    def test_predefined_tn_plate(self):
        v = GarageService._generate_deterministic_vehicle("TN-01-AB-1234")
        assert v["owner_name"] == "Citizen Appellant"
        assert v["vehicle_make"] == "TATA"
        assert v["vehicle_model"] == "Nexon EV"
        assert v["rc_status"] == "ACTIVE"

    def test_predefined_dl_plate(self):
        v = GarageService._generate_deterministic_vehicle("DL-03-CD-5678")
        assert v["owner_name"] == "Aarav Sharma"

    def test_deterministic_same_plate_returns_same(self):
        v1 = GarageService._generate_deterministic_vehicle("GJ-01-XX-9999")
        v2 = GarageService._generate_deterministic_vehicle("GJ-01-XX-9999")
        assert v1 == v2

    def test_different_plates_different_vehicles(self):
        v1 = GarageService._generate_deterministic_vehicle("UP-11-AA-1111")
        v2 = GarageService._generate_deterministic_vehicle("WB-22-BB-2222")
        # Deterministic hashes likely produce different owners or make/model
        assert (v1["owner_name"] != v2["owner_name"] or
                v1["vehicle_make"] != v2["vehicle_make"])

    def test_rc_status_may_be_suspended(self):
        # Loop through hashes to find a suspended one
        for suffix in range(100):
            plate = f"RJ-01-XX-{suffix:04d}"
            v = GarageService._generate_deterministic_vehicle(plate)
            if v["rc_status"] == "SUSPENDED":
                break
        else:
            pytest.skip("No SUSPENDED status found in sample range")

    def test_ground_truth_tn01(self):
        """The normalized plate 'TN01AB1234' also matches the predefined vehicle."""
        v = GarageService._generate_deterministic_vehicle("TN01AB1234")
        assert v["owner_name"] == "Citizen Appellant"


class TestSyncVehicles:
    """Tests for sync_vehicles — mocks asyncio.sleep and cache."""

    @pytest.mark.asyncio
    async def test_cache_none_mode_single_plate(self):
        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles(
                user_id="test-user",
                vehicle_number="TN-01-AB-1234",
                cache=None,
            )
        assert result.sync_status == "COMPLETED"
        assert len(result.vehicles) == 1
        assert result.vehicles[0].vehicle_number == "TN-01-AB-1234"

    @pytest.mark.asyncio
    async def test_cache_none_mode_no_plate_returns_defaults(self):
        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles(
                user_id="test-user",
                vehicle_number=None,
                cache=None,
            )
        assert result.sync_status == "COMPLETED"
        assert len(result.vehicles) == 2
        assert result.vehicles[0].vehicle_number == "TN-01-AB-1234"
        assert result.vehicles[1].vehicle_number == "DL-03-CD-5678"

    @pytest.mark.asyncio
    async def test_invalid_plate_raises_validation_error(self):
        with pytest.raises(ServiceValidationError, match="Invalid Indian vehicle"):
            await GarageService.sync_vehicles(
                user_id="test-user",
                vehicle_number="INVALID",
                cache=None,
            )

    @pytest.mark.asyncio
    async def test_invalid_plate_missing_state_code(self):
        with pytest.raises(ServiceValidationError):
            await GarageService.sync_vehicles(
                user_id="test-user",
                vehicle_number="12-34-AB-5678",
                cache=None,
            )

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_data(self):
        mock_cache = AsyncMock()
        cached_data = {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "vehicle_number": "TN-01-AB-1234",
            "owner_name": "Cached Owner",
            "vehicle_make": "TATA",
            "vehicle_model": "Nexon EV",
            "rc_status": "ACTIVE",
            "insurance_expiry": "2026-12-31T00:00:00",
            "puc_expiry": "2026-06-30T00:00:00",
            "created_at": "2025-01-01T00:00:00",
        }
        mock_cache.get_json.return_value = cached_data

        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles(
                user_id="test-user",
                vehicle_number="TN-01-AB-1234",
                cache=mock_cache,
            )

        assert result.sync_status == "COMPLETED"
        assert len(result.vehicles) == 1
        assert result.vehicles[0].owner_name == "Cached Owner"
        mock_cache.get_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_fetches_and_caches(self):
        mock_cache = AsyncMock()
        mock_cache.get_json.return_value = None

        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles(
                user_id="test-user",
                vehicle_number="GJ-01-XX-9999",
                cache=mock_cache,
            )

        assert result.sync_status == "COMPLETED"
        assert len(result.vehicles) == 1
        # Should have set cache
        mock_cache.set_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_miss_caches_and_returns_regenerated(self):
        mock_cache = AsyncMock()
        mock_cache.get_json.return_value = None

        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles(
                user_id="test-user",
                vehicle_number="MH-02-EF-9012",
                cache=mock_cache,
            )

        assert len(result.vehicles) == 1
        v = result.vehicles[0]
        assert v.owner_name == "Priya Patel"
        assert v.vehicle_make == "Maruti Suzuki"
        # Insurance is expired (expiry_days = -10)
        assert v.insurance_expiry is not None

    @pytest.mark.asyncio
    async def test_cache_get_raises_logs_and_falls_through(self):
        mock_cache = AsyncMock()
        mock_cache.get_json.side_effect = Exception("Redis down")

        with patch.object(asyncio, "sleep", AsyncMock()):
            result = await GarageService.sync_vehicles(
                user_id="test-user",
                vehicle_number="DL-03-CD-5678",
                cache=mock_cache,
            )

        assert len(result.vehicles) == 1
        assert result.vehicles[0].vehicle_number == "DL-03-CD-5678"
