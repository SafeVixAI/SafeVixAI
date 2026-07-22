# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Request
from mcp.server.fastmcp import FastMCP
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from starlette.routing import Mount, Route

from core.rbac import Role, require_role

logger = logging.getLogger("safevixai.mcp")

mcp = FastMCP("SafeVixAI")

# ---------------------------------------------------------------------------
# MCP Authentication & Rate Limiting
# ---------------------------------------------------------------------------

_MCP_RATE_LIMIT = 10          # max requests per window
_MCP_RATE_WINDOW = 60         # seconds
_rate_store: dict[str, list[float]] = defaultdict(list)


def _check_mcp_auth(request: StarletteRequest) -> bool:
    """Return True if the request carries a valid admin JWT cookie."""
    from core.config import get_settings
    if get_settings().environment == "test":
        return True
    token = request.cookies.get("access_token")
    if not token:
        return False
    try:
        from core.security import _decode_bearer_token
        user = _decode_bearer_token(token)
        return user.get("role") in ("admin", "operator")
    except Exception:
        return False


def _check_mcp_rate_limit(request: StarletteRequest) -> bool:
    """Return True if the caller is within the rate limit."""
    client_ip = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window_start = now - _MCP_RATE_WINDOW
    timestamps = _rate_store[client_ip]
    # Remove old timestamps outside the window
    _rate_store[client_ip] = [t for t in timestamps if t > window_start]
    if len(_rate_store[client_ip]) >= _MCP_RATE_LIMIT:
        return False
    _rate_store[client_ip].append(now)
    return True


async def _mcp_auth_middleware(request: StarletteRequest, call_next: Any) -> Response:
    """Starlette middleware that enforces MCP authentication and rate limiting."""
    if not _check_mcp_rate_limit(request):
        logger.warning("MCP rate limit exceeded for %s", request.client)
        return Response("Rate limit exceeded. Max 10 requests/minute.", status_code=429)
    if not _check_mcp_auth(request):
        logger.warning(
            "MCP unauthorized request from %s (path=%s)",
            getattr(request.client, "host", "?"),
            request.url.path,
        )
        return Response(
            "Unauthorized. Admin or Operator role required.",
            status_code=403,
        )
    return await call_next(request)


# FastAPI dependency for the /mcp_info router
# Phase 0.1: Replace X-Admin-Key with RBAC
async def require_mcp_admin(
    request: Request,
    user: dict = Depends(require_role(Role.ADMIN)),
) -> dict:
    """FastAPI dependency: validates admin role for /mcp_info endpoints."""
    return user


def _valid_lat_lon(lat: float, lon: float) -> bool:
    return -90 <= lat <= 90 and -180 <= lon <= 180 and not (lat == 0 and lon == 0)


async def _build_roadwatch_service() -> tuple[Any, Any, Any, Any]:
    from core.config import get_settings
    from core.redis_client import create_cache
    from services.authority_router import AuthorityRouter
    from services.geocoding_service import GeocodingService
    from services.overpass_service import OverpassService
    from services.roadwatch_service import RoadWatchService

    settings = get_settings()
    cache = create_cache(settings.redis_url)
    overpass = OverpassService(settings)
    geocoding = GeocodingService(settings, cache)
    authority = AuthorityRouter(settings, overpass, cache)
    service = RoadWatchService(
        settings=settings,
        cache=cache,
        geocoding_service=geocoding,
        authority_router=authority,
    )
    return service, cache, overpass, geocoding


@mcp.tool()
async def get_emergency_services(lat: float, lon: float, radius: int = 5000) -> str:
    """Get nearby emergency services for a location, expanding coverage when needed."""
    if not _valid_lat_lon(lat, lon):
        return "Invalid coordinates. Latitude must be -90..90, longitude -180..180, and not 0,0."

    from core.config import get_settings
    from core.redis_client import create_cache
    from services.emergency_locator import EmergencyLocatorService
    from services.overpass_service import OverpassService

    settings = get_settings()
    cache = create_cache(settings.redis_url)
    overpass = OverpassService(settings)
    try:
        service = EmergencyLocatorService(settings=settings, cache=cache, overpass_service=overpass)
        facilities = await service.get_nearby_facilities(lat, lon, max(100, min(radius, settings.max_radius)))
        if not facilities:
            return "No emergency services found within 25km. Call 112 for national emergency dispatch."

        lines = [f"Found {len(facilities)} emergency services near {lat:.5f},{lon:.5f}:"]
        for item in facilities[:10]:
            flags = ", ".join(
                flag
                for flag, enabled in (
                    ("trauma", item.has_trauma),
                    ("ICU", item.has_icu),
                    ("24hr", item.is_24hr),
                )
                if enabled
            )
            suffix = f" [{flags}]" if flags else ""
            phone = item.phone_emergency or item.phone or "N/A"
            lines.append(
                f"- {item.name} ({item.category}){suffix}: {int(item.distance_meters)}m, phone {phone}"
            )
        return "\n".join(lines)
    except Exception as exc:
        logger.exception("MCP emergency lookup failed")
        return f"Failed to fetch emergency services: {exc}"
    finally:
        await overpass.aclose()
        await cache.close()


@mcp.tool()
async def report_road_issue(issue_type: str, severity: int, lat: float, lon: float, description: str = "") -> str:
    """Report a RoadWatch hazard using the same validated service path as the public API."""
    if not _valid_lat_lon(lat, lon):
        return "Invalid coordinates. Refusing to create a report."
    if not 1 <= severity <= 5:
        return "Invalid severity. Use a value from 1 to 5."

    from core.database import get_async_session

    service, cache, overpass, geocoding = await _build_roadwatch_service()
    try:
        async for session in get_async_session():
            result = await service.submit_report(
                db=session,
                lat=lat,
                lon=lon,
                issue_type=issue_type,
                severity=severity,
                description=f"[MCP Agent] {description}".strip(),
                photo=None,
            )
            return (
                f"Reported {issue_type} severity {severity}/5 at {lat:.5f},{lon:.5f}. "
                f"Issue ID: {result.uuid}. Complaint ref: {result.complaint_ref or 'pending'}"
            )
        return "Failed to report road issue: database session unavailable."
    except Exception as exc:
        logger.exception("MCP road issue report failed")
        return f"Failed to report road issue: {exc}"
    finally:
        await geocoding.aclose()
        await overpass.aclose()
        await cache.close()


@mcp.tool()
async def calculate_challan(
    vehicle_type: str,
    offense_type: str,
    previous_offenses: int = 0,
    state_code: str = "TN",
) -> str:
    """Calculate an MV Act challan estimate using the backend ChallanService."""
    import inspect

    from core.config import get_settings
    from models.schemas import ChallanQuery, ChallanResponse
    from services.challan_service import ChallanService

    offense_aliases = {
        "speeding": "183",
        "red_light": "179",
        "helmet": "194D",
        "seatbelt": "194D",
        "drunk_driving": "185",
        "dui": "185",
        "no_license": "181",
        "mobile_use": "179",
        "overloading": "179",
        "pollution": "179",
        "no_insurance": "179",
    }
    violation_code = offense_aliases.get(offense_type.strip().lower(), offense_type)
    service = ChallanService(get_settings())
    try:
        candidate = service.calculate(
            ChallanQuery(
                violation_code=violation_code,
                vehicle_class=vehicle_type,
                state_code=state_code,
                is_repeat=previous_offenses > 0,
            )
        )
        if inspect.isawaitable(candidate):
            candidate = await candidate
        if not isinstance(candidate, ChallanResponse):
            raise TypeError("Unexpected challan result shape")
        result = candidate
    except Exception as exc:
        legacy = getattr(service, "calculate_fine", None)
        if legacy is None:
            logger.exception("MCP challan calculation failed")
            return f"Could not calculate challan: {exc}"
        try:
            legacy_result = legacy(vehicle_type, offense_type, previous_offenses)
            if inspect.isawaitable(legacy_result):
                legacy_result = await legacy_result
            if "error" in legacy_result:
                return f"Could not calculate challan: {legacy_result['error']}"
            return (
                "Traffic challan estimate\n"
                f"Offense: {offense_type} | Vehicle: {vehicle_type}\n"
                f"Fine: INR {legacy_result.get('fine_amount', 'Unknown')}\n"
                f"MV Act section: {legacy_result.get('mv_act_section', 'N/A')}\n"
                f"Description: {legacy_result.get('description', 'N/A')}"
            )
        except Exception as legacy_exc:
            logger.exception("MCP challan legacy calculation failed")
            return f"Could not calculate challan: {legacy_exc}"

    repeat_note = " Repeat offense pricing applied." if previous_offenses > 0 else ""
    override_note = f" {result.state_override}." if result.state_override else ""
    return (
        "Traffic challan estimate\n"
        f"Offense: {offense_type} ({result.violation_code})\n"
        f"Vehicle: {result.vehicle_class}, state: {result.state_code}\n"
        f"Fine: INR {result.amount_due}.{repeat_note}{override_note}\n"
        f"MV Act section: {result.section}\n"
        f"Description: {result.description}"
    )


@mcp.tool()
async def get_road_weather(lat: float, lon: float) -> str:
    """Get current road-weather conditions from Open-Meteo."""
    if not _valid_lat_lon(lat, lon):
        return "Invalid coordinates."
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": "temperature_2m,relative_humidity_2m,precipitation,rain,snowfall,weather_code,wind_speed_10m,visibility",
                    "wind_speed_unit": "kmh",
                    "timezone": "Asia/Kolkata",
                },
            )
            resp.raise_for_status()
        current = resp.json().get("current", {})
        rain = float(current.get("rain") or 0)
        precipitation = float(current.get("precipitation") or 0)
        wind = float(current.get("wind_speed_10m") or 0)
        visibility = float(current.get("visibility") or 10000)
        risk = "LOW"
        warnings: list[str] = []
        if rain > 5 or precipitation > 5 or visibility < 1000 or wind > 50:
            risk = "HIGH"
        elif rain > 0.5 or precipitation > 0.5 or visibility < 3000:
            risk = "MODERATE"
        if rain > 0.5:
            warnings.append("wet roads")
        if visibility < 3000:
            warnings.append("reduced visibility")
        if wind > 50:
            warnings.append("strong wind")
        return (
            f"Road weather risk: {risk}. "
            f"Temp {current.get('temperature_2m', 'N/A')} C, rain {rain}mm, "
            f"wind {wind} km/h, visibility {visibility/1000:.1f}km. "
            f"Warnings: {', '.join(warnings) if warnings else 'none'}."
        )
    except Exception as exc:
        logger.exception("MCP weather lookup failed")
        return f"Weather data unavailable: {exc}"


@mcp.tool()
async def calculate_safe_route(
    origin_lat: float,
    origin_lon: float,
    dest_lat: float,
    dest_lon: float,
    avoid_accidents: bool = True,
) -> str:
    """Calculate an OSM-backed route summary. RoadWatch hazard weighting is noted when enabled."""
    if not (_valid_lat_lon(origin_lat, origin_lon) and _valid_lat_lon(dest_lat, dest_lon)):
        return "Invalid route coordinates."
    try:
        url = (
            "https://router.project-osrm.org/route/v1/driving/"
            f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
        )
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params={"overview": "false", "steps": "true", "annotations": "false"})
            resp.raise_for_status()
        routes = resp.json().get("routes", [])
        if not routes:
            return "No route found between those coordinates."
        route = routes[0]
        steps = route.get("legs", [{}])[0].get("steps", [])[:5]
        instructions = []
        for step in steps:
            maneuver = step.get("maneuver", {})
            road = step.get("name") or "unnamed road"
            instructions.append(f"- {maneuver.get('type', 'continue')} {maneuver.get('modifier', '')} on {road}".strip())
        hazard_note = " RoadWatch hazard avoidance should be checked before dispatch." if avoid_accidents else ""
        return (
            f"Distance {route['distance']/1000:.1f} km, ETA {route['duration']/60:.0f} min."
            f"{hazard_note}\n"
            + "\n".join(instructions or ["No turn steps returned."])
        )
    except Exception as exc:
        logger.exception("MCP route calculation failed")
        return f"Routing unavailable: {exc}"


@mcp.tool()
async def get_first_aid_guide(injury_type: str, crash_severity: str = "moderate") -> str:
    """Return concise first-aid guidance for road-crash injuries."""
    guides = {
        "bleeding": [
            "Apply firm direct pressure with clean cloth.",
            "Do not remove soaked cloth; add more layers.",
            "Keep the person warm and still.",
            "Call 108 immediately.",
        ],
        "unconscious": [
            "Check response and breathing.",
            "If not breathing, start CPR: 30 compressions then 2 breaths.",
            "If breathing, keep airway open and monitor continuously.",
            "Call 108 immediately.",
        ],
        "fracture": [
            "Do not straighten the limb.",
            "Immobilize above and below the injury.",
            "Cover open wounds with clean cloth.",
            "Call 108 for transport.",
        ],
        "spinal_injury": [
            "Do not move the person unless there is immediate danger.",
            "Keep head, neck, and spine aligned.",
            "Monitor breathing.",
            "Tell 108 dispatch spinal injury is suspected.",
        ],
        "burn": [
            "Cool with running water for 20 minutes.",
            "Remove nearby jewelry before swelling.",
            "Cover loosely with clean plastic or cloth.",
            "Do not apply toothpaste, butter, or creams.",
        ],
    }
    key = injury_type.lower().replace(" ", "_").replace("-", "_")
    steps = guides.get(key) or guides.get("bleeding")
    severity_note = " Treat as high priority after a severe crash." if crash_severity.lower() == "severe" else ""
    return (
        f"First aid: {injury_type}.{severity_note}\n"
        + "\n".join(f"{idx}. {step}" for idx, step in enumerate(steps or [], start=1))
        + "\nThis is general guidance only. Call 108/112 immediately."
    )


@mcp.tool()
async def get_location_from_what3words(words: str) -> str:
    """Convert a What3Words address to GPS coordinates using the server-side API key."""
    from core.config import get_settings

    cleaned = words.strip().lstrip("/").lower()
    if cleaned.startswith("///"):
        cleaned = cleaned[3:]
    if cleaned.count(".") != 2:
        return "Invalid What3Words address. Expected three words separated by dots."

    api_key = getattr(get_settings(), "w3w_api_key", None)
    if not api_key:
        return f"What3Words API key is not configured. Try https://map.what3words.com/{cleaned}"
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://api.what3words.com/v3/convert-to-coordinates",
                params={"words": cleaned, "language": "en", "format": "json", "key": api_key},
            )
            resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            return f"What3Words error: {data['error'].get('message', 'Unknown error')}"
        coords = data.get("coordinates", {})
        lat = coords.get("lat")
        lon = coords.get("lng")
        return f"///{cleaned} -> {lat},{lon}. Maps: https://www.google.com/maps?q={lat},{lon}"
    except Exception as exc:
        logger.exception("MCP What3Words lookup failed")
        return f"What3Words lookup failed: {exc}"


_sse_transport = SseServerTransport("/mcp/messages/")


async def _handle_sse(request: StarletteRequest) -> None:
    async with _sse_transport.connect_sse(
        request.scope,
        request.receive,
        request._send,
    ) as streams:
        await mcp._mcp_server.run(
            streams[0],
            streams[1],
            mcp._mcp_server.create_initialization_options(),
        )


# Starlette sub-application for MCP — protected by auth middleware
sse_app = Starlette(
    routes=[
        Route("/sse", endpoint=_handle_sse),
        Mount("/messages/", app=_sse_transport.handle_post_message),
    ],
    middleware=[
        # Import here to avoid circular issues at module load time
        __import__("starlette.middleware", fromlist=["Middleware"]).Middleware(
            __import__("starlette.middleware.base", fromlist=["BaseHTTPMiddleware"]).BaseHTTPMiddleware,
            dispatch=_mcp_auth_middleware,
        )
    ],
)


router = APIRouter(prefix="/mcp_info", tags=["MCP Server"])


@router.get("/", dependencies=[Depends(require_mcp_admin)])
async def get_mcp_info() -> dict[str, Any]:
    """Return MCP server metadata. Requires Admin role."""
    return {
        "service": "SafeVixAI MCP Server",
        "mounted_at": "/mcp",
        "sse_endpoint": "/mcp/sse",
        "messages_endpoint": "/mcp/messages/",
        "auth": "Admin or Operator JWT role required",
        "rate_limit": f"{_MCP_RATE_LIMIT} requests per {_MCP_RATE_WINDOW}s",
        "tools": [
            "get_emergency_services",
            "report_road_issue",
            "calculate_challan",
            "get_road_weather",
            "calculate_safe_route",
            "get_first_aid_guide",
            "get_location_from_what3words",
        ],
    }


@router.get("/health")
async def get_mcp_health() -> dict[str, Any]:
    """Health check endpoint for MCP server integration."""
    try:
        return {
            "status": "healthy",
            "mcp_server": "online",
            "transport": "sse",
            "tools_count": len(mcp._mcp_server.tools) if hasattr(mcp._mcp_server, "tools") else 7,
        }
    except Exception as exc:
        logger.exception("MCP health check failed")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"MCP health check failed: {exc}") from exc

