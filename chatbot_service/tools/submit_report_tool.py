# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""SubmitReportTool — wires chat assistant road reports directly to the backend API.

The assistant calls this tool when the user wants to report a road hazard
(pothole, crack, broken signage, etc.) via the chat interface.
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

# Max size for base64-encoded photo in the tool payload (64 KB text, ~48 KB binary)
_MAX_B64_PHOTO_LEN = 65_536


class SubmitReportTool:
    """Submits road issue reports to the backend `/api/v1/roads/report` endpoint.

    Requires `backend_base_url` to be set (injected from chatbot Settings).
    Falls back to guidance-only mode if the backend URL is not configured.
    """

    def __init__(self, backend_base_url: str | None = None) -> None:
        self._base_url = (backend_base_url or '').rstrip('/')
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    async def aclose(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def submit(
        self,
        *,
        issue_type: str,
        severity: str = 'medium',
        description: str = '',
        lat: float | None = None,
        lon: float | None = None,
    ) -> dict:
        """Submit a road issue report.  Returns a result dict with status/id.

        If the backend is unreachable or not configured, returns guidance instead
        so the assistant can still give a helpful response.
        """
        if not self._base_url:
            return self._guidance(issue_type, lat, lon)

        severity_value = self._normalize_severity(severity)
        payload: dict = {
            'issue_type': issue_type,
            'severity': str(severity_value),
            'description': description or f'Reported via chat assistant: {issue_type}',
        }
        if lat is not None and lon is not None:
            payload['lat'] = lat
            payload['lon'] = lon

        # Guard: truncate description if it somehow contains an oversized encoded blob
        if len(payload.get('description', '')) > _MAX_B64_PHOTO_LEN:
            payload['description'] = payload['description'][:_MAX_B64_PHOTO_LEN]

        try:
            headers = {}
            from config import get_settings
            settings = get_settings()
            if settings.internal_api_key:  # pragma: no branch
                headers['X-Internal-Api-Key'] = settings.internal_api_key

            resp = await self._get_client().post(
                f'{self._base_url}/api/v1/roads/report',
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                'submitted': True,
                'report_id': data.get('uuid') or data.get('id') or data.get('report_id'),
                'complaint_ref': data.get('complaint_ref'),
                'message': (
                    'Report submitted successfully. '
                    f"Complaint reference: {data.get('complaint_ref') or data.get('uuid', 'N/A')}"
                ),
                'issue_type': issue_type,
            }
        except httpx.HTTPStatusError as exc:
            logger.warning('SubmitReportTool HTTP error %s: %s', exc.response.status_code, exc)
            return self._guidance(issue_type, lat, lon, error='Backend returned an error. Please use the app report form.')
        except Exception as exc:
            logger.warning('SubmitReportTool failed: %s', exc)
            return self._guidance(issue_type, lat, lon)

    def build_guidance(
        self,
        *,
        issue_type: str,
        lat: float | None = None,
        lon: float | None = None,
    ) -> dict:
        """Legacy guidance-only method (used when no backend URL configured)."""
        return self._guidance(issue_type, lat, lon)

    @staticmethod
    def _guidance(
        issue_type: str,
        lat: float | None,
        lon: float | None,
        error: str | None = None,
    ) -> dict:
        coords = f'{lat:.5f}, {lon:.5f}' if lat is not None and lon is not None else 'your current location'
        msg = error or (
            f'Prepare a road issue report for "{issue_type}" at {coords}. '
            'Open the Report tab in the app to attach a photo and set severity.'
        )
        return {'submitted': False, 'summary': msg, 'issue_type': issue_type}

    @staticmethod
    def _normalize_severity(value: str | int) -> int:
        if isinstance(value, int):
            return min(5, max(1, value))
        normalized = value.strip().lower()
        mapping = {
            'low': 1,
            'minor': 1,
            'medium': 2,
            'moderate': 2,
            'high': 4,
            'critical': 5,
            'severe': 5,
        }
        if normalized.isdigit():
            return min(5, max(1, int(normalized)))
        return mapping.get(normalized, 2)
