# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""LGD Directory ingestor — fetches India's admin hierarchy via NAPIX API or CSV fallback."""

from __future__ import annotations

import csv
import io
import logging
from typing import Any

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.lgd_entity import LGDEntity
from services.civic_intel.base_ingestor import BaseIngestor

logger = logging.getLogger(__name__)

# NAPIX LGD API endpoints discovered from dev.napix.gov.in/nic/lgd/product
NAPIX_BASE = 'https://api.napix.gov.in/nic/lgd'
NAPIX_ENDPOINTS = {
    'states': f'{NAPIX_BASE}/states',
    'activeStates': f'{NAPIX_BASE}/activeStates',
    'districts': f'{NAPIX_BASE}/districts',
    'activeDistrictsByState': f'{NAPIX_BASE}/activeDistrictsByState',
    'subdistricts': f'{NAPIX_BASE}/subdistricts',
    'activeSubdistrictsbyState': f'{NAPIX_BASE}/activeSubdistrictsbyState',
    'blocks': f'{NAPIX_BASE}/blocks',
    'activeBlocksByState': f'{NAPIX_BASE}/activeBlocksByState',
    'localbodiesByState': f'{NAPIX_BASE}/localbodiesByState',
    'villages': f'{NAPIX_BASE}/villages',
    'villagesByState': f'{NAPIX_BASE}/villagesByState',
    'activeVillagesByState': f'{NAPIX_BASE}/activeVillagesByState',
    'wardsByState': f'{NAPIX_BASE}/wardsByState',
    'wardsByStateByCategoryU': f'{NAPIX_BASE}/wardsByStateByCategoryU',
    'wardsByStateByCategoryT': f'{NAPIX_BASE}/wardsByStateByCategoryT',
    'cantonmentBoards': f'{NAPIX_BASE}/cantonmentBoards',
    'cantonmentBoardsByState': f'{NAPIX_BASE}/cantonmentBoardsByState',
    'parliamentConstituencyByState': f'{NAPIX_BASE}/parliamentConstituencyByState',
    'assemblyConstituencyByState': f'{NAPIX_BASE}/assemblyConstituencyByState',
}

# Indian state codes for iteration
INDIAN_STATE_CODES = [
    '01', '02', '03', '04', '05', '06', '07', '08', '09', '10',
    '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
    '21', '22', '23', '24', '25', '26', '27', '28', '29', '30',
    '31', '32', '33', '34', '35', '36', '37', '38',
]


class LGDIngestor(BaseIngestor):
    """Ingests LGD directory data via NAPIX API (preferred) or CSV bulk download (fallback).

    NAPIX API provides:
    - Real-time data (not stale CSVs)
    - State-filtered queries (no need to download everything)
    - Duration-based delta queries for incremental updates
    - 13 product groups with 50+ endpoints
    """

    @property
    def name(self) -> str:
        return 'lgd'

    async def fetch(self) -> list[dict[str, Any]]:
        """Fetch LGD entities — tries NAPIX API first, falls back to CSV."""
        settings = get_settings()

        if settings.lgd_api_key:
            return await self._fetch_via_napix(settings.lgd_api_key)
        else:
            logger.info('[LGD] No LGD_API_KEY set — falling back to CSV download')
            return await self._fetch_via_csv()

    async def _fetch_via_napix(self, api_key: str) -> list[dict[str, Any]]:
        """Fetch from NAPIX LGD API — state → district → subdistrict → block → ULB."""
        all_records: list[dict[str, Any]] = []
        headers = {'Authorization': f'Bearer {api_key}', 'Accept': 'application/json'}

        async with self._get_http_client() as client:
            # 1. Fetch all states
            try:
                resp = await client.get(NAPIX_ENDPOINTS['activeStates'], headers=headers)
                resp.raise_for_status()
                states = resp.json()
                for state in states if isinstance(states, list) else states.get('data', []):
                    all_records.append({
                        'lgd_code': state.get('stateCode') or state.get('lgdCode'),
                        'entity_type': 'state',
                        'name_en': state.get('stateName') or state.get('name', ''),
                        'name_local': state.get('stateNameLocal'),
                        'parent_lgd_code': None,
                        'state_code': str(state.get('stateCode', '')).zfill(2),
                        'census_code_2011': state.get('censusCode2011'),
                    })
                logger.info('[LGD:NAPIX] Fetched %d states', len(all_records))
            except Exception as exc:
                logger.warning('[LGD:NAPIX] States fetch failed: %s', exc)

            # 2. Fetch districts per state
            for state_code in INDIAN_STATE_CODES:
                try:
                    resp = await client.get(
                        NAPIX_ENDPOINTS['activeDistrictsByState'],
                        params={'stateCode': state_code},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        districts = resp.json()
                        items = districts if isinstance(districts, list) else districts.get('data', [])
                        for d in items:
                            all_records.append({
                                'lgd_code': d.get('districtCode') or d.get('lgdCode'),
                                'entity_type': 'district',
                                'name_en': d.get('districtName') or d.get('name', ''),
                                'name_local': d.get('districtNameLocal'),
                                'parent_lgd_code': int(state_code),
                                'state_code': state_code,
                                'census_code_2011': d.get('censusCode2011'),
                            })
                except Exception as exc:
                    logger.warning('[LGD:NAPIX] Districts for state %s failed: %s', state_code, exc)

            logger.info('[LGD:NAPIX] Total records after districts: %d', len(all_records))

            # 3. Fetch subdistricts per state
            for state_code in INDIAN_STATE_CODES:
                try:
                    resp = await client.get(
                        NAPIX_ENDPOINTS['activeSubdistrictsbyState'],
                        params={'stateCode': state_code},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        items = resp.json()
                        items = items if isinstance(items, list) else items.get('data', [])
                        for sd in items:
                            all_records.append({
                                'lgd_code': sd.get('subdistrictCode') or sd.get('lgdCode'),
                                'entity_type': 'subdistrict',
                                'name_en': sd.get('subdistrictName') or sd.get('name', ''),
                                'name_local': sd.get('subdistrictNameLocal'),
                                'parent_lgd_code': sd.get('districtCode'),
                                'state_code': state_code,
                                'census_code_2011': sd.get('censusCode2011'),
                            })
                except Exception as exc:
                    logger.debug('[LGD:NAPIX] Subdistrict fetch for state %s failed: %s', state_code, exc)

            # 4. Fetch blocks per state
            for state_code in INDIAN_STATE_CODES:
                try:
                    resp = await client.get(
                        NAPIX_ENDPOINTS['activeBlocksByState'],
                        params={'stateCode': state_code},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        items = resp.json()
                        items = items if isinstance(items, list) else items.get('data', [])
                        for blk in items:
                            all_records.append({
                                'lgd_code': blk.get('blockCode') or blk.get('lgdCode'),
                                'entity_type': 'block',
                                'name_en': blk.get('blockName') or blk.get('name', ''),
                                'name_local': blk.get('blockNameLocal'),
                                'parent_lgd_code': blk.get('districtCode'),
                                'state_code': state_code,
                            })
                except Exception as exc:
                    logger.debug("LGD ingestor — block fetch failed for state %s: %s", state_code, exc)

            # 5. Fetch local bodies (ULBs) per state
            for state_code in INDIAN_STATE_CODES:
                try:
                    resp = await client.get(
                        NAPIX_ENDPOINTS['localbodiesByState'],
                        params={'stateCode': state_code},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        items = resp.json()
                        items = items if isinstance(items, list) else items.get('data', [])
                        for ulb in items:
                            all_records.append({
                                'lgd_code': ulb.get('localBodyCode') or ulb.get('lgdCode'),
                                'entity_type': 'ulb',
                                'name_en': ulb.get('localBodyName') or ulb.get('name', ''),
                                'name_local': ulb.get('localBodyNameLocal'),
                                'parent_lgd_code': ulb.get('districtCode'),
                                'state_code': state_code,
                                'census_code_2011': ulb.get('censusCode2011'),
                            })
                except Exception as exc:
                    logger.debug("LGD ingestor — ULB fetch failed for state %s: %s", state_code, exc)

        logger.info('[LGD:NAPIX] Total fetched: %d entities', len(all_records))
        return all_records

    async def _fetch_via_csv(self) -> list[dict[str, Any]]:
        """Fallback: Download LGD CSV files from lgdirectory.gov.in."""
        settings = get_settings()
        all_records: list[dict[str, Any]] = []

        csv_urls = {
            'state': f'{settings.lgd_csv_base_url}?entityType=State',
            'district': f'{settings.lgd_csv_base_url}?entityType=District',
            'subdistrict': f'{settings.lgd_csv_base_url}?entityType=SubDistrict',
            'block': f'{settings.lgd_csv_base_url}?entityType=Block',
        }

        for entity_type, url in csv_urls.items():
            try:
                resp = await self._fetch_with_retry(url)
                reader = csv.DictReader(io.StringIO(resp.text))
                for row in reader:
                    lgd_code = row.get('LGD Code') or row.get('Entity LGD Code') or row.get('Code')
                    if not lgd_code:
                        continue
                    all_records.append({
                        'lgd_code': int(lgd_code),
                        'entity_type': entity_type,
                        'name_en': row.get('Name (In English)') or row.get('Entity Name') or '',
                        'name_local': row.get('Name (In Local)'),
                        'parent_lgd_code': int(row['Parent LGD Code']) if row.get('Parent LGD Code') else None,
                        'state_code': str(row.get('State LGD Code', '')).zfill(2),
                        'census_code_2011': row.get('Census 2011 Code'),
                        'population_census_2011': int(row['Census 2011 Population']) if row.get('Census 2011 Population') else None,
                    })
                logger.info('[LGD:CSV] Fetched %d %s entities', len(all_records), entity_type)
            except Exception as exc:
                logger.warning('[LGD:CSV] Failed to download %s CSV: %s', entity_type, exc)

        return all_records

    async def transform(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Normalize and deduplicate by lgd_code."""
        seen: set[int] = set()
        clean: list[dict[str, Any]] = []
        for r in raw:
            code = r.get('lgd_code')
            if code and code not in seen:
                seen.add(code)
                r['is_active'] = True
                clean.append(r)
        return clean

    async def load(
        self, db: AsyncSession, records: list[dict[str, Any]],
    ) -> tuple[int, int, int]:
        """Upsert LGD entities by lgd_code."""
        inserted, updated, skipped = 0, 0, 0

        for record in records:
            try:
                stmt = pg_insert(LGDEntity).values(**record)
                stmt = stmt.on_conflict_do_update(
                    index_elements=['lgd_code'],
                    set_={
                        'name_en': stmt.excluded.name_en,
                        'name_local': stmt.excluded.name_local,
                        'parent_lgd_code': stmt.excluded.parent_lgd_code,
                        'state_code': stmt.excluded.state_code,
                        'is_active': stmt.excluded.is_active,
                    },
                )
                result = await db.execute(stmt)
                if result.rowcount > 0:
                    inserted += 1
                else:
                    updated += 1
            except Exception as exc:
                logger.debug('[LGD] Skip record %s: %s', record.get('lgd_code'), exc)
                skipped += 1

        return inserted, updated, skipped
