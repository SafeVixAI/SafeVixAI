# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
import sys
from pathlib import Path

import httpx

from config import Settings

# alert_service.py is at project root
for parent in Path(__file__).resolve().parents:  # pragma: no branch
    if (parent / 'alert_service.py').exists():
        if str(parent) not in sys.path:
            sys.path.insert(0, str(parent))
        break
from core.alert import get_alert_service  # noqa: E402

logger = logging.getLogger("safevixai.chatbot.tools")


class BackendToolClient:
    def __init__(self, settings: Settings) -> None:
        headers = {
            'Accept': 'application/json',
            'User-Agent': settings.http_user_agent,
        }
        if settings.internal_api_key:
            headers['X-Internal-Api-Key'] = settings.internal_api_key
        self._client = httpx.AsyncClient(
            base_url=settings.main_backend_base_url,
            timeout=settings.main_backend_timeout_seconds,
            headers=headers,
        )

    async def get(self, path: str, *, params: dict | None = None) -> dict | None:
        try:
            response = await self._client.get(path, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("Backend GET %s failed with HTTP %s", path, status)
            if status >= 500:
                get_alert_service().alert_external_api_failed(
                    service_name="Backend API",
                    endpoint=f"GET {path}",
                    status_code=status,
                    error_msg=str(exc),
                )
            return None
        except httpx.RequestError as exc:
            logger.exception("Backend GET %s request failed", path)
            get_alert_service().alert_external_api_failed(
                service_name="Backend API",
                endpoint=f"GET {path}",
                status_code=0,
                error_msg=f"Connection error: {exc}",
            )
            return None
        except ValueError:
            logger.exception("Backend GET %s returned invalid JSON", path)
            return None

    async def post(self, path: str, *, payload: dict | None = None) -> dict | None:
        try:
            response = await self._client.post(path, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.warning("Backend POST %s failed with HTTP %s", path, status)
            if status >= 500:
                get_alert_service().alert_external_api_failed(
                    service_name="Backend API",
                    endpoint=f"POST {path}",
                    status_code=status,
                    error_msg=str(exc),
                )
            return None
        except httpx.RequestError as exc:
            logger.exception("Backend POST %s request failed", path)
            get_alert_service().alert_external_api_failed(
                service_name="Backend API",
                endpoint=f"POST {path}",
                status_code=0,
                error_msg=f"Connection error: {exc}",
            )
            return None
        except ValueError:
            logger.exception("Backend POST %s returned invalid JSON", path)
            return None

    async def aclose(self) -> None:
        await self._client.aclose()


from tools.challan_tool import ChallanTool  # noqa: E402
from tools.drug_info import DrugInfoTool  # noqa: E402
from tools.first_aid_tool import FirstAidTool  # noqa: E402
from tools.geocoding import GeocodingClient  # noqa: E402
from tools.legal_search_tool import LegalSearchTool  # noqa: E402
from tools.open_meteo import OpenMeteoClient  # noqa: E402
from tools.road_infra_tool import RoadInfrastructureTool  # noqa: E402
from tools.road_issues_tool import RoadIssuesTool  # noqa: E402
from tools.sos_tool import SosTool  # noqa: E402
from tools.submit_report_tool import SubmitReportTool  # noqa: E402
from tools.weather_tool import WeatherTool  # noqa: E402
from tools.what3words import What3WordsTool  # noqa: E402

__all__ = [
    'BackendToolClient',
    'ChallanTool',
    'DrugInfoTool',
    'FirstAidTool',
    'GeocodingClient',
    'LegalSearchTool',
    'OpenMeteoClient',
    'RoadInfrastructureTool',
    'RoadIssuesTool',
    'SosTool',
    'SubmitReportTool',
    'WeatherTool',
    'What3WordsTool',
]
