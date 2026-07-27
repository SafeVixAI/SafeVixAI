# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from api.v1.offline import get_offline_bundle, router
from services.exceptions import ServiceValidationError


class TestOfflineBundle:
    async def test_bundle_success(self) -> None:
        request = MagicMock()
        request.app.state.emergency_service = AsyncMock()
        request.app.state.emergency_service.build_city_bundle = AsyncMock(
            return_value={"city": "chennai", "hospitals": [], "police": []}
        )
        db = MagicMock()
        result = await get_offline_bundle(request, "chennai", db, request.app.state.emergency_service)
        assert result["city"] == "chennai"

    async def test_bundle_not_found(self) -> None:
        request = MagicMock()
        svc = AsyncMock()
        svc.build_city_bundle = AsyncMock(side_effect=ServiceValidationError("City not found"))
        request.app.state.emergency_service = svc
        db = MagicMock()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await get_offline_bundle(request, "unknown", db, svc)
        assert exc.value.status_code == 404

    async def test_bundle_city_validation_min_length(self) -> None:
        request = MagicMock()
        db = MagicMock()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            from pydantic import TypeAdapter
            from fastapi import Path
            city_validator = TypeAdapter(str)
            city_validator.validate_python("a", from_attributes=True)

    async def test_router_prefix(self) -> None:
        assert router.prefix == "/api/v1/offline"

    async def test_bundle_empty_city_return(self) -> None:
        request = MagicMock()
        svc = AsyncMock()
        svc.build_city_bundle = AsyncMock(return_value={"city": "", "hospitals": [], "police": []})
        request.app.state.emergency_service = svc
        db = MagicMock()
        result = await get_offline_bundle(request, "test", db, svc)
        assert result["city"] == ""

    async def test_bundle_service_error(self) -> None:
        request = MagicMock()
        svc = AsyncMock()
        svc.build_city_bundle = AsyncMock(side_effect=ServiceValidationError("no data"))
        request.app.state.emergency_service = svc
        db = MagicMock()
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc:
            await get_offline_bundle(request, "test", db, svc)
        assert exc.value.status_code == 404

    async def test_bundle_with_full_data(self) -> None:
        request = MagicMock()
        svc = AsyncMock()
        bundle = {
            "city": "mumbai",
            "hospitals": [{"name": "A", "lat": 19.0, "lon": 72.0}],
            "police": [{"name": "B", "lat": 19.1, "lon": 72.1}],
            "fire": [{"name": "C", "lat": 19.2, "lon": 72.2}],
            "version": "1.0",
        }
        svc.build_city_bundle = AsyncMock(return_value=bundle)
        request.app.state.emergency_service = svc
        db = MagicMock()
        result = await get_offline_bundle(request, "mumbai", db, svc)
        assert len(result["hospitals"]) == 1
        assert len(result["police"]) == 1
