# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Tests for MCP server tools — uses lazy imports to avoid module-level hang in pytest."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture(autouse=True)
def reset_mcp_module():
    """Force re-import api.v1.mcp_server for each test to ensure clean state."""
    # Clear from sys.modules to force fresh import
    import sys
    for key in list(sys.modules.keys()):
        if "mcp_server" in key or "fastmcp" in key or "mcp.server" in key:
            del sys.modules[key]
    yield


def _get_mcp():
    """Lazy import api.v1.mcp_server and return the mcp instance."""
    from api.v1 import mcp_server
    return mcp_server.mcp


@pytest.mark.asyncio
@patch("services.challan_service.ChallanService")
async def test_mcp_calculate_challan_tool(mock_challan_class):
    """Unit test for the MCP calculate_challan tool logic."""
    mock_instance = AsyncMock()
    mock_instance.calculate_fine.return_value = {
        "fine_amount": "1000",
        "mv_act_section": "185",
        "consequences": ["Jail", "Fine"],
        "description": "Drunk Driving",
    }
    mock_challan_class.return_value = mock_instance

    mcp = _get_mcp()

    # FastMCP stores tools in _tool_manager
    tools = mcp._tool_manager._tools
    tool = tools.get("calculate_challan")
    assert tool is not None, "calculate_challan tool not registered"
    fn = tool.fn

    result = await fn(vehicle_type="4W", offense_type="drunk_driving", previous_offenses=0)

    assert "₹1000" in result or "1000" in result
    assert "185" in result


@pytest.mark.asyncio
async def test_mcp_report_road_issue_tool():
    """Unit test for the MCP report_road_issue tool logic."""
    mcp = _get_mcp()

    tools = mcp._tool_manager._tools
    tool = tools.get("report_road_issue")
    assert tool is not None, "report_road_issue tool not registered"
    fn = tool.fn

    # Call — will fail at DB insert (no real DB) but should still return a string
    result = await fn(issue_type="pothole", severity=4, lat=13.0, lon=80.0, description="Deep pothole")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_mcp_get_emergency_services_tool():
    """Smoke test: tool is registered and callable; external services will fail gracefully."""
    mcp = _get_mcp()

    tools = mcp._tool_manager._tools
    tool = tools.get("get_emergency_services")
    assert tool is not None, "get_emergency_services tool not registered"
    fn = tool.fn

    # Will fail on real HTTP/Redis calls — but should return a string, not raise
    result = await fn(lat=13.0678, lon=80.2785, radius=2000)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_mcp_road_weather_tool():
    """Test that road weather tool is registered and returns a message."""
    mcp = _get_mcp()

    tools = mcp._tool_manager._tools
    tool = tools.get("get_road_weather")
    assert tool is not None, "get_road_weather tool not registered"
    fn = tool.fn

    result = await fn(lat=13.0, lon=80.0)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_mcp_safe_route_tool():
    """Test that safe route tool is registered and returns a message."""
    mcp = _get_mcp()

    tools = mcp._tool_manager._tools
    tool = tools.get("calculate_safe_route")
    assert tool is not None, "calculate_safe_route tool not registered"
    fn = tool.fn

    result = await fn(origin_lat=13.0, origin_lon=80.0, dest_lat=13.1, dest_lon=80.1)
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_mcp_first_aid_tool():
    """Test that first aid tool is registered and returns guidance."""
    mcp = _get_mcp()

    tools = mcp._tool_manager._tools
    tool = tools.get("get_first_aid_guide")
    assert tool is not None, "get_first_aid_guide tool not registered"
    fn = tool.fn

    result = await fn(injury_type="bleeding")
    assert isinstance(result, str)
    assert "Call" in result


@pytest.mark.asyncio
async def test_mcp_what3words_tool():
    """Test that what3words tool is registered."""
    mcp = _get_mcp()

    tools = mcp._tool_manager._tools
    tool = tools.get("get_location_from_what3words")
    assert tool is not None, "get_location_from_what3words tool not registered"
    fn = tool.fn

    # No API key configured in test — should return error message, not crash
    result = await fn(words="filled.count.soap")
    assert isinstance(result, str)


@pytest.mark.asyncio
async def test_mcp_all_tools_registered():
    """Test that all expected MCP tools are registered."""
    mcp = _get_mcp()

    tools = mcp._tool_manager._tools
    expected_tools = {
        "get_emergency_services",
        "report_road_issue",
        "calculate_challan",
        "get_road_weather",
        "calculate_safe_route",
        "get_first_aid_guide",
        "get_location_from_what3words",
    }
    registered = set(tools.keys())
    assert expected_tools.issubset(registered), f"Missing tools: {expected_tools - registered}"
    assert len(registered) >= len(expected_tools), f"Expected at least {len(expected_tools)} tools, got {len(registered)}"
