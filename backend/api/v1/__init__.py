# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from fastapi import APIRouter

from api.v1.admin import router as admin_router
from api.v1.analytics import router as analytics_router
from api.v1.auth import router as auth_router
from api.v1.authority import router as authority_router
from api.v1.challan import router as challan_router
from api.v1.chat import router as chat_router
from api.v1.circuit_breaker_api import router as circuit_breaker_router
from api.v1.citizen import router as citizen_router
from api.v1.civic_intel import router as civic_intel_router
from api.v1.command_center import router as command_center_router
from api.v1.emergency import router as emergency_router
from api.v1.field_workflow import router as field_workflow_router
from api.v1.garage import router as garage_router
from api.v1.geocode import router as geocode_router
from api.v1.live_tracking import router as live_tracking_router
from api.v1.officers import router as officers_router
from api.v1.offline import router as offline_router
from api.v1.providers import router as providers_router
from api.v1.public import router as public_router
from api.v1.roadwatch import router as roadwatch_router
from api.v1.routing import router as routing_router
from api.v1.tracking import router as tracking_router
from api.v1.probes import router as probes_router
from api.v1.updates import router as updates_router
from api.v1.user import router as user_router
from api.v1.wards import router as wards_router
from api.v1.waze_feed import router as waze_feed_router

api_router = APIRouter()
api_router.include_router(chat_router)
api_router.include_router(challan_router)
api_router.include_router(emergency_router)
api_router.include_router(roadwatch_router)
api_router.include_router(geocode_router)
api_router.include_router(offline_router)
api_router.include_router(routing_router)
api_router.include_router(user_router)
api_router.include_router(tracking_router)
api_router.include_router(auth_router)
api_router.include_router(live_tracking_router)
api_router.include_router(waze_feed_router)
api_router.include_router(circuit_breaker_router)
api_router.include_router(wards_router)
api_router.include_router(analytics_router)
api_router.include_router(officers_router)
api_router.include_router(admin_router)
api_router.include_router(civic_intel_router)
api_router.include_router(authority_router)
api_router.include_router(field_workflow_router)
api_router.include_router(citizen_router)
api_router.include_router(public_router)
api_router.include_router(command_center_router)
api_router.include_router(garage_router)
api_router.include_router(providers_router)
api_router.include_router(updates_router)
api_router.include_router(probes_router)

