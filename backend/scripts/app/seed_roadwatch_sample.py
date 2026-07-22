# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
import uuid

from geoalchemy2.elements import WKTElement
from sqlalchemy.dialects.postgresql import insert

from core.database import AsyncSessionLocal
from models.road_issue import RoadInfrastructure, RoadIssue

SAMPLE_INFRASTRUCTURE = [
    {
        'road_id': 'sample-nh32-chennai',
        'road_name': 'Grand Southern Trunk Road',
        'road_type': 'National Highway',
        'road_number': 'NH32',
        'length_km': 2.4,
        'geometry': WKTElement('LINESTRING(80.245 13.020, 80.290 13.070)', srid=4326),
        'state_code': 'TN',
        'contractor_name': 'ABC Infra Projects',
        'exec_engineer': 'R. Kumar',
        'exec_engineer_phone': '9000000001',
        'budget_sanctioned': 50000000,
        'budget_spent': 32000000,
        'project_source': 'sample_seed',
        'data_source_url': 'https://example.org/nh32',
    },
    {
        'road_id': 'sample-sh49-chennai',
        'road_name': 'East Coast Road',
        'road_type': 'State Highway',
        'road_number': 'SH49',
        'length_km': 3.1,
        'geometry': WKTElement('LINESTRING(80.255 13.000, 80.330 13.040)', srid=4326),
        'state_code': 'TN',
        'contractor_name': 'Seaside Roads Ltd',
        'exec_engineer': 'M. Priya',
        'exec_engineer_phone': '9000000002',
        'budget_sanctioned': 42000000,
        'budget_spent': 15000000,
        'project_source': 'sample_seed',
        'data_source_url': 'https://example.org/sh49',
    },
]

SAMPLE_ISSUES = [
    {
        'uuid': uuid.UUID('11111111-1111-4111-8111-111111111111'),
        'issue_type': 'pothole',
        'severity': 4,
        'description': 'Large pothole near the service road merge.',
        'location': WKTElement('POINT(80.271 13.043)', srid=4326),
        'location_address': 'GST Road, Chennai',
        'road_name': 'Grand Southern Trunk Road',
        'road_type': 'National Highway',
        'road_number': 'NH32',
        'authority_name': 'NHAI',
        'authority_phone': '1033',
        'complaint_ref': 'RS-SAMPLE-001',
        'status': 'open',
    },
    {
        'uuid': uuid.UUID('22222222-2222-4222-8222-222222222222'),
        'issue_type': 'waterlogging',
        'severity': 3,
        'description': 'Standing water after rain near junction.',
        'location': WKTElement('POINT(80.302 13.020)', srid=4326),
        'location_address': 'East Coast Road, Chennai',
        'road_name': 'East Coast Road',
        'road_type': 'State Highway',
        'road_number': 'SH49',
        'authority_name': 'State PWD',
        'authority_phone': '1800-180-6763',
        'complaint_ref': 'RS-SAMPLE-002',
        'status': 'in_progress',
    },
]


async def main() -> None:
    async with AsyncSessionLocal() as session:
        infra_stmt = insert(RoadInfrastructure).values(SAMPLE_INFRASTRUCTURE)
        infra_upsert = infra_stmt.on_conflict_do_update(
            index_elements=['road_id'],
            set_={
                'road_name': infra_stmt.excluded.road_name,
                'road_type': infra_stmt.excluded.road_type,
                'road_number': infra_stmt.excluded.road_number,
                'geometry': infra_stmt.excluded.geometry,
                'state_code': infra_stmt.excluded.state_code,
                'contractor_name': infra_stmt.excluded.contractor_name,
                'exec_engineer': infra_stmt.excluded.exec_engineer,
                'exec_engineer_phone': infra_stmt.excluded.exec_engineer_phone,
                'budget_sanctioned': infra_stmt.excluded.budget_sanctioned,
                'budget_spent': infra_stmt.excluded.budget_spent,
                'project_source': infra_stmt.excluded.project_source,
                'data_source_url': infra_stmt.excluded.data_source_url,
            },
        )
        await session.execute(infra_upsert)

        issue_stmt = insert(RoadIssue).values(SAMPLE_ISSUES)
        issue_upsert = issue_stmt.on_conflict_do_nothing(index_elements=['uuid'])
        await session.execute(issue_upsert)
        await session.commit()

    print(f'Seeded {len(SAMPLE_INFRASTRUCTURE)} road segments and {len(SAMPLE_ISSUES)} sample road issues.')


if __name__ == '__main__':
    asyncio.run(main())
