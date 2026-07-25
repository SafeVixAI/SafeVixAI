# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Coverage tests for tools: submit_report_tool, first_aid_tool."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from config import get_settings
from tools.first_aid_tool import FirstAidTool
from tools.submit_report_tool import SubmitReportTool


class TestSubmitReportToolCoverage:
    """SubmitReportTool — client re-creation, API key, build_guidance."""

    @pytest.fixture
    def tool(self) -> SubmitReportTool:
        return SubmitReportTool(backend_base_url="http://backend:8000")

    @pytest.mark.asyncio
    async def test_get_client_recreates_when_closed(self, tool: SubmitReportTool):
        """_get_client creates new client when previous was closed."""
        client1 = tool._get_client()
        assert client1 is not None
        await tool.aclose()
        assert tool._client.is_closed is True
        client2 = tool._get_client()
        assert client2 is not client1

    @pytest.mark.asyncio
    async def test_internal_api_key_header(self, tool: SubmitReportTool):
        """X-Internal-Api-Key header is injected when internal_api_key is set."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {"uuid": "abc-123", "complaint_ref": "CR-001"}

        mock_client = MagicMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.is_closed = False

        with patch.object(tool, "_get_client", return_value=mock_client):
            with patch("config.get_settings") as mock_get_settings:
                mock_settings = MagicMock()
                mock_settings.internal_api_key = "secret-key"
                mock_get_settings.return_value = mock_settings

                result = await tool.submit(
                    issue_type="pothole",
                    severity="high",
                    description="Large pothole",
                    lat=12.34,
                    lon=56.78,
                )

        call_kwargs = mock_client.post.call_args[1]
        assert call_kwargs["headers"].get("X-Internal-Api-Key") == "secret-key"
        assert result["submitted"] is True
        assert result["report_id"] == "abc-123"
        assert result["complaint_ref"] == "CR-001"

    def test_build_guidance_legacy(self, tool: SubmitReportTool):
        """Legacy build_guidance returns guidance dict."""
        result = tool.build_guidance(issue_type="pothole", lat=12.34, lon=56.78)
        assert result["submitted"] is False
        assert "pothole" in result["summary"]


class TestFirstAidToolCoverage:
    """FirstAidTool — fallback when file missing, corrupt JSON, list normalization."""

    def test_fallback_when_file_missing(self, tmp_path: Path):
        """Missing first_aid.json returns FALLBACK_GUIDES."""
        settings = get_settings().model_copy(update={"rag_data_dir": tmp_path})
        tool = FirstAidTool(settings)
        guide = tool.lookup("bleeding")
        assert guide is not None
        assert guide["title"] == "Severe bleeding"

    def test_fallback_on_corrupt_json(self, tmp_path: Path):
        """Corrupt JSON returns FALLBACK_GUIDES."""
        (tmp_path / "first_aid.json").write_text("this is not json", encoding="utf-8")
        settings = get_settings().model_copy(update={"rag_data_dir": tmp_path})
        tool = FirstAidTool(settings)
        guide = tool.lookup("burn")
        assert guide is not None
        assert "title" in guide
        assert "steps" in guide

    def test_fallback_on_empty_list_payload(self, tmp_path: Path):
        """Empty list payload returns FALLBACK_GUIDES."""
        (tmp_path / "first_aid.json").write_text("[]", encoding="utf-8")
        settings = get_settings().model_copy(update={"rag_data_dir": tmp_path})
        tool = FirstAidTool(settings)
        guide = tool.lookup("burn")
        assert guide is not None
        assert "title" in guide

    def test_fallback_on_list_with_no_valid_articles(self, tmp_path: Path):
        """List with no valid articles returns FALLBACK_GUIDES."""
        (tmp_path / "first_aid.json").write_text(
            json.dumps([{"id": "", "title": "", "steps": []}]),
            encoding="utf-8",
        )
        settings = get_settings().model_copy(update={"rag_data_dir": tmp_path})
        tool = FirstAidTool(settings)
        guide = tool.lookup("cpr")
        assert guide is not None
        assert "title" in guide

    def test_normalize_article_list(self):
        """List payload normalization produces correct guide dicts."""
        payload = [
            {
                "id": "test_1",
                "title": "Test Guide",
                "category": "first-aid",
                "steps": ["Step 1", "Step 2"],
                "warning": "Be careful",
                "call_ambulance_if": ["Severe pain"],
            }
        ]
        result = FirstAidTool._normalize_article_list(payload)
        assert "test_1" in result
        assert result["test_1"]["title"] == "Test Guide"
        assert result["test_1"]["steps"] == ["Step 1", "Step 2"]
        assert result["test_1"]["warning"] == "Be careful"
        assert result["test_1"]["call_ambulance_if"] == ["Severe pain"]

    def test_normalize_article_list_skips_invalid_entries(self):
        """List normalization skips non-dict entries and missing titles."""
        payload = [
            "not a dict",
            {"title": "", "steps": []},
            {"id": "valid", "title": "Valid Guide", "steps": ["Do something"]},
        ]
        result = FirstAidTool._normalize_article_list(payload)
        assert "valid" in result
        assert len(result) == 1
