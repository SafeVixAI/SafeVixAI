# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

from dataclasses import dataclass

from geoalchemy2 import Geography
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import Settings
from core.redis_client import CacheHelper
from models.road_issue import RoadInfrastructure
from models.schemas import AuthorityPreviewResponse
from services.exceptions import ExternalServiceError
from services.overpass_service import OverpassService, RoadContext


@dataclass(frozen=True, slots=True)
class AuthorityInfo:
    authority_name: str
    helpline: str
    complaint_portal: str
    escalation_path: str


AUTHORITY_MATRIX: dict[str, AuthorityInfo] = {
    'NH': AuthorityInfo('NHAI', '1033', 'https://nhai.gov.in/complaint', 'Ministry of Road Transport'),
    'SH': AuthorityInfo('State PWD', '1800-180-6763', 'https://pgportal.gov.in', 'State Transport Minister'),
    'MDR': AuthorityInfo('District Collector / DRDA', '1076', 'https://pgportal.gov.in', 'District Magistrate'),
    'VILLAGE': AuthorityInfo('PMGSY / Gram Panchayat', '1800-180-6763', 'https://ommas.nic.in', 'Block Development Officer'),
    'URBAN': AuthorityInfo('Municipal Corporation', '1800-11-0012', 'https://pgportal.gov.in', 'Municipal Commissioner'),
}

ROAD_TYPE_LABELS = {
    'NH': 'National Highway',
    'SH': 'State Highway',
    'MDR': 'Major District Road',
    'VILLAGE': 'Village Road',
    'URBAN': 'Urban Road',
}


class AuthorityRouter:
    def __init__(self, settings: Settings, overpass_service: OverpassService, cache: CacheHelper) -> None:
        self.settings = settings
        self.overpass_service = overpass_service
        self.cache = cache

    async def resolve(self, *, db: AsyncSession, lat: float, lon: float) -> AuthorityPreviewResponse:
        infrastructure = await self._lookup_infrastructure(db=db, lat=lat, lon=lon)
        if infrastructure is not None:
            road_type_code = self.normalize_road_type(infrastructure.road_type, infrastructure.road_number)
            authority = AUTHORITY_MATRIX[road_type_code]
            return AuthorityPreviewResponse(
                road_type=ROAD_TYPE_LABELS[road_type_code],
                road_type_code=road_type_code,
                road_name=infrastructure.road_name,
                road_number=infrastructure.road_number,
                authority_name=authority.authority_name,
                helpline=authority.helpline,
                complaint_portal=authority.complaint_portal,
                escalation_path=authority.escalation_path,
                exec_engineer=infrastructure.exec_engineer,
                exec_engineer_phone=infrastructure.exec_engineer_phone,
                contractor_name=infrastructure.contractor_name,
                budget_sanctioned=infrastructure.budget_sanctioned,
                budget_spent=infrastructure.budget_spent,
                last_relayed_date=infrastructure.last_relayed_date,
                next_maintenance=infrastructure.next_maintenance,
                data_source_url=infrastructure.data_source_url,
                source='road_infrastructure',
            )

        try:
            road_context = await self.overpass_service.get_road_context(lat=lat, lon=lon)
        except ExternalServiceError:
            return self._fallback_preview()
        if road_context is None:
            return self._fallback_preview()
        return self._from_road_context(road_context)

    async def _lookup_infrastructure(
        self,
        *,
        db: AsyncSession,
        lat: float,
        lon: float,
        radius_meters: int = 100,
    ) -> RoadInfrastructure | None:
        point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)
        point_geography = cast(point, Geography)
        geometry_geography = cast(RoadInfrastructure.geometry, Geography)
        distance_expr = func.ST_Distance(geometry_geography, point_geography)

        stmt = (
            select(RoadInfrastructure)
            .where(func.ST_DWithin(geometry_geography, point_geography, radius_meters))
            .order_by(distance_expr.asc())
            .limit(1)
        )
        return (await db.execute(stmt)).scalar_one_or_none()

    def _from_road_context(self, road_context: RoadContext) -> AuthorityPreviewResponse:
        authority = AUTHORITY_MATRIX[road_context.road_type_code]
        return AuthorityPreviewResponse(
            road_type=road_context.road_type,
            road_type_code=road_context.road_type_code,
            road_name=road_context.road_name,
            road_number=road_context.road_number,
            authority_name=authority.authority_name,
            helpline=authority.helpline,
            complaint_portal=authority.complaint_portal,
            escalation_path=authority.escalation_path,
            source='overpass',
        )

    def _fallback_preview(self) -> AuthorityPreviewResponse:
        authority = AUTHORITY_MATRIX['URBAN']
        return AuthorityPreviewResponse(
            road_type=ROAD_TYPE_LABELS['URBAN'],
            road_type_code='URBAN',
            authority_name=authority.authority_name,
            helpline=authority.helpline,
            complaint_portal=authority.complaint_portal,
            escalation_path=authority.escalation_path,
            source='fallback',
        )

    @staticmethod
    def normalize_road_type(road_type: str | None, road_number: str | None) -> str:
        text = (road_type or '').upper()
        number = (road_number or '').upper()
        if 'NH' in text or number.startswith('NH'):
            return 'NH'
        if 'STATE HIGHWAY' in text or text == 'SH' or number.startswith('SH'):
            return 'SH'
        if 'MDR' in text or 'DISTRICT' in text or number.startswith('MDR'):
            return 'MDR'
        if 'VILLAGE' in text or 'PMGSY' in text:
            return 'VILLAGE'
        return 'URBAN'
