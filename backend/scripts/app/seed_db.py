# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

from geoalchemy2.elements import WKTElement
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from core.config import get_settings
from models.emergency import EmergencyService

settings = get_settings()

connect_args = (
    {'prepared_statement_cache_size': 0}
    if settings.database_url.startswith('postgresql+asyncpg://')
    else {}
)

engine: AsyncEngine = create_async_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout_seconds,
    pool_recycle=settings.db_pool_recycle_seconds,
    future=True,
)

SessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)

# name, category, sub_category, city, district, state, state_code, address, phone,
# phone_emergency, lat, lon, has_trauma, has_icu, bed_count, rating
SEED_DATA: list[tuple] = [
    ('Apollo Hospital Greams Road', 'hospital', 'Multi-specialty Hospital', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Greams Road, Chennai', '044-28293333', '108', 13.0636, 80.2518, True, True, 550, 4.7),
    ('Government General Hospital Chennai', 'hospital', 'Government Tertiary Hospital', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Park Town, Chennai', '044-25305000', '108', 13.0806, 80.2767, True, True, 3000, 4.2),
    ('MIOT International Hospital', 'hospital', 'Specialty Hospital', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Manapakkam, Chennai', '044-42002288', '108', 13.0203, 80.1856, True, True, 1000, 4.6),
    ('Sri Ramachandra Medical Centre', 'hospital', 'Teaching Hospital', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Porur, Chennai', '044-45928500', '108', 13.0396, 80.1749, True, True, 1200, 4.5),
    ('Fortis Malar Hospital Adyar', 'hospital', 'Multi-specialty Hospital', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Adyar, Chennai', '044-42892222', '108', 13.0067, 80.2572, True, True, 180, 4.3),
    ('Manipal Hospital Old Airport Road', 'hospital', 'Multi-specialty Hospital', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Old Airport Road, Bengaluru', '080-25024444', '108', 12.9580, 77.6490, True, True, 650, 4.6),
    ("St John's Medical College Hospital", 'hospital', 'Teaching Hospital', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Sarjapur Road, Bengaluru', '080-49466000', '108', 12.9352, 77.6229, True, True, 1350, 4.5),
    ('Narayana Health City', 'hospital', 'Cardiac and Multi-specialty Hospital', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Bommasandra, Bengaluru', '080-71222222', '108', 12.8096, 77.6967, True, True, 1500, 4.6),
    ('Victoria Hospital Bengaluru', 'hospital', 'Government General Hospital', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Fort Road, Bengaluru', '080-26701150', '108', 12.9642, 77.5733, True, True, 1000, 4.1),
    ('Apollo Hospital Bannerghatta Road', 'hospital', 'Multi-specialty Hospital', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Bannerghatta Road, Bengaluru', '080-26304050', '108', 12.8960, 77.5993, True, True, 250, 4.4),
    ('KEM Hospital Parel', 'hospital', 'Government Teaching Hospital', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Parel, Mumbai', '022-24107000', '108', 19.0029, 72.8416, True, True, 1800, 4.3),
    ('Lilavati Hospital Bandra', 'hospital', 'Multi-specialty Hospital', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Bandra West, Mumbai', '022-26751000', '108', 19.0510, 72.8295, True, True, 350, 4.5),
    ('Kokilaben Dhirubhai Ambani Hospital', 'hospital', 'Quaternary Care Hospital', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Andheri West, Mumbai', '022-42696969', '108', 19.1354, 72.8278, True, True, 750, 4.7),
    ('Sir H.N. Reliance Foundation Hospital', 'hospital', 'Multi-specialty Hospital', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Girgaon, Mumbai', '022-61305000', '108', 18.9586, 72.8072, True, True, 345, 4.6),
    ('Tata Memorial Hospital Parel', 'hospital', 'Oncology Tertiary Hospital', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Parel, Mumbai', '022-24177000', '108', 18.9978, 72.8427, False, True, 650, 4.5),
    ('AIIMS New Delhi Trauma Centre', 'hospital', 'Government Trauma Centre', 'Delhi', 'New Delhi', 'Delhi', 'DL', 'Ansari Nagar, New Delhi', '011-26588500', '102', 28.5672, 77.2100, True, True, 950, 4.6),
    ('Safdarjung Hospital', 'hospital', 'Government General Hospital', 'Delhi', 'New Delhi', 'Delhi', 'DL', 'Ansari Nagar West, New Delhi', '011-26730000', '102', 28.5704, 77.2073, True, True, 1600, 4.2),
    ('Ram Manohar Lohia Hospital', 'hospital', 'Government Referral Hospital', 'Delhi', 'New Delhi', 'Delhi', 'DL', 'Baba Kharak Singh Marg, New Delhi', '011-23365525', '102', 28.6257, 77.2001, True, True, 1400, 4.2),
    ('Lok Nayak Hospital Delhi Gate', 'hospital', 'Government Teaching Hospital', 'Delhi', 'Central Delhi', 'Delhi', 'DL', 'Delhi Gate, New Delhi', '011-23236000', '102', 28.6431, 77.2383, True, True, 1800, 4.1),
    ('Max Super Speciality Hospital Saket', 'hospital', 'Super Specialty Hospital', 'Delhi', 'South Delhi', 'Delhi', 'DL', 'Saket, New Delhi', '011-26515050', '102', 28.5275, 77.2149, True, True, 530, 4.6),
    ('Teynampet Police Station', 'police', 'Law and Order Police Station', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Anna Salai, Chennai', '044-24343080', '100', 13.0435, 80.2503, False, False, None, 4.1),
    ('Mylapore Police Station', 'police', 'Law and Order Police Station', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Mylapore, Chennai', '044-28475100', '100', 13.0334, 80.2697, False, False, None, 4.0),
    ('Adyar Police Station', 'police', 'Law and Order Police Station', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Adyar, Chennai', '044-24412544', '100', 13.0084, 80.2576, False, False, None, 4.1),
    ('Cubbon Park Police Station', 'police', 'City Police Station', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Cubbon Park, Bengaluru', '080-22942566', '100', 12.9764, 77.5950, False, False, None, 4.2),
    ('Indiranagar Police Station', 'police', 'City Police Station', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Indiranagar, Bengaluru', '080-22942530', '100', 12.9719, 77.6412, False, False, None, 4.1),
    ('Whitefield Police Station', 'police', 'City Police Station', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Whitefield, Bengaluru', '080-22942600', '100', 12.9698, 77.7499, False, False, None, 4.0),
    ('Electronic City Police Station', 'police', 'City Police Station', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Electronic City, Bengaluru', '080-22942700', '100', 12.8420, 77.6600, False, False, None, 3.9),
    ('Dadar Police Station', 'police', 'City Police Station', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Dadar West, Mumbai', '022-24143366', '100', 19.0178, 72.8434, False, False, None, 4.0),
    ('Bandra Police Station', 'police', 'City Police Station', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Bandra West, Mumbai', '022-26423120', '100', 19.0544, 72.8400, False, False, None, 4.1),
    ('Andheri Police Station', 'police', 'City Police Station', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Andheri East, Mumbai', '022-26843000', '100', 19.1197, 72.8468, False, False, None, 4.0),
    ('Colaba Police Station', 'police', 'City Police Station', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Colaba, Mumbai', '022-22180998', '100', 18.9067, 72.8147, False, False, None, 4.2),
    ('Connaught Place Police Station', 'police', 'District Police Station', 'Delhi', 'New Delhi', 'Delhi', 'DL', 'Connaught Place, New Delhi', '011-23490201', '100', 28.6315, 77.2167, False, False, None, 4.1),
    ('Hauz Khas Police Station', 'police', 'District Police Station', 'Delhi', 'South Delhi', 'Delhi', 'DL', 'Hauz Khas, New Delhi', '011-26853800', '100', 28.5498, 77.1911, False, False, None, 4.0),
    ('Lajpat Nagar Police Station', 'police', 'District Police Station', 'Delhi', 'South East Delhi', 'Delhi', 'DL', 'Lajpat Nagar, New Delhi', '011-29837000', '100', 28.5670, 77.2430, False, False, None, 4.0),
    ('Dwarka North Police Station', 'police', 'District Police Station', 'Delhi', 'South West Delhi', 'Delhi', 'DL', 'Dwarka Sector 23, New Delhi', '011-28042000', '100', 28.5968, 77.0507, False, False, None, 3.9),
    ('Tamil Nadu 108 Ambulance Chennai Central', 'ambulance', 'Public Emergency Ambulance', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Central Chennai Dispatch', '108', '108', 13.0867, 80.2707, False, False, None, 4.4),
    ('GVK EMRI Ambulance Dispatch Chennai South', 'ambulance', 'Emergency Dispatch Hub', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Velachery, Chennai', '108', '108', 12.9848, 80.2170, False, False, None, 4.3),
    ('Apollo Ambulance Services Chennai', 'ambulance', 'Private Critical Care Ambulance', 'Chennai', 'Chennai', 'Tamil Nadu', 'TN', 'Greams Road, Chennai', '1066', '108', 13.0604, 80.2519, False, False, None, 4.4),
    ('Karnataka 108 Ambulance Bengaluru Central', 'ambulance', 'Public Emergency Ambulance', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Central Bengaluru Dispatch', '108', '108', 12.9715, 77.5944, False, False, None, 4.4),
    ('Aster Ambulance Services Bengaluru', 'ambulance', 'Private Emergency Ambulance', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Hebbal, Bengaluru', '080-46691000', '108', 12.9828, 77.6057, False, False, None, 4.3),
    ('Manipal Ambulance Response Bengaluru', 'ambulance', 'Critical Care Ambulance', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Old Airport Road, Bengaluru', '080-25024444', '108', 12.9578, 77.6488, False, False, None, 4.3),
    ('Narayana Ambulance Dispatch Bommasandra', 'ambulance', 'Hospital Ambulance Hub', 'Bengaluru', 'Bengaluru Urban', 'Karnataka', 'KA', 'Bommasandra, Bengaluru', '080-71222222', '108', 12.8105, 77.6950, False, False, None, 4.2),
    ('108 Emergency Ambulance Mumbai Central', 'ambulance', 'Public Emergency Ambulance', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Central Mumbai Dispatch', '108', '108', 18.9696, 72.8193, False, False, None, 4.4),
    ('Mumbai Ambulance Service Parel', 'ambulance', 'Municipal Ambulance Service', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Parel, Mumbai', '022-24136051', '108', 19.0076, 72.8420, False, False, None, 4.2),
    ('Kokilaben Ambulance Services Andheri', 'ambulance', 'Critical Care Ambulance', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Andheri West, Mumbai', '022-42696969', '108', 19.1360, 72.8274, False, False, None, 4.3),
    ('Lilavati Ambulance Services Bandra', 'ambulance', 'Hospital Ambulance Service', 'Mumbai', 'Mumbai', 'Maharashtra', 'MH', 'Bandra Reclamation, Mumbai', '022-26751000', '108', 19.0516, 72.8292, False, False, None, 4.3),
    ('CATS Ambulance HQ Delhi', 'ambulance', 'Public Emergency Ambulance', 'Delhi', 'Central Delhi', 'Delhi', 'DL', 'Central Delhi Dispatch', '102', '102', 28.6448, 77.2167, False, False, None, 4.5),
    ('AIIMS Ambulance Services Delhi', 'ambulance', 'Hospital Emergency Ambulance', 'Delhi', 'New Delhi', 'Delhi', 'DL', 'Ansari Nagar, New Delhi', '011-26588500', '102', 28.5676, 77.2095, False, False, None, 4.4),
    ('Fortis Ambulance Services Vasant Kunj', 'ambulance', 'Private Emergency Ambulance', 'Delhi', 'South West Delhi', 'Delhi', 'DL', 'Vasant Kunj, New Delhi', '011-42776222', '102', 28.5279, 77.1552, False, False, None, 4.2),
    ('Max Ambulance Dispatch Saket', 'ambulance', 'Hospital Ambulance Service', 'Delhi', 'South Delhi', 'Delhi', 'DL', 'Saket, New Delhi', '011-26515050', '102', 28.5282, 77.2154, False, False, None, 4.2),
]


def _build_rows() -> list[dict]:
    if len(SEED_DATA) != 50:
        raise ValueError(f'Expected exactly 50 rows but found {len(SEED_DATA)}')

    seeded_at = datetime.now(UTC).replace(tzinfo=None)
    rows: list[dict] = []

    for idx, row in enumerate(SEED_DATA, start=1):
        (
            name,
            category,
            sub_category,
            city,
            district,
            state,
            state_code,
            address,
            phone,
            phone_emergency,
            lat,
            lon,
            has_trauma,
            has_icu,
            bed_count,
            rating,
        ) = row

        rows.append(
            {
                'osm_id': 990_000_000 + idx,
                'osm_type': 'seed',
                'name': name,
                'category': category,
                'sub_category': sub_category,
                'address': address,
                'phone': phone,
                'phone_emergency': phone_emergency,
                'location': WKTElement(f'POINT({lon} {lat})', srid=4326),
                'city': city,
                'district': district,
                'state': state,
                'state_code': state_code,
                'country_code': 'IN',
                'is_24hr': True,
                'has_trauma': has_trauma,
                'has_icu': has_icu,
                'bed_count': bed_count,
                'rating': rating,
                'source': 'seed_db_script',
                'raw_tags': {'seeded': True, 'seed_group': 'indian_metros'},
                'verified': False,
                'last_updated': seeded_at,
                'created_at': seeded_at,
            }
        )

    return rows


async def seed_emergency_services() -> int:
    rows = _build_rows()

    async with SessionLocal() as session:
        stmt = insert(EmergencyService).values(rows)
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=['osm_id'],
            set_={
                'osm_type': stmt.excluded.osm_type,
                'name': stmt.excluded.name,
                'category': stmt.excluded.category,
                'sub_category': stmt.excluded.sub_category,
                'address': stmt.excluded.address,
                'phone': stmt.excluded.phone,
                'phone_emergency': stmt.excluded.phone_emergency,
                'location': stmt.excluded.location,
                'city': stmt.excluded.city,
                'district': stmt.excluded.district,
                'state': stmt.excluded.state,
                'state_code': stmt.excluded.state_code,
                'country_code': stmt.excluded.country_code,
                'is_24hr': stmt.excluded.is_24hr,
                'has_trauma': stmt.excluded.has_trauma,
                'has_icu': stmt.excluded.has_icu,
                'bed_count': stmt.excluded.bed_count,
                'rating': stmt.excluded.rating,
                'source': stmt.excluded.source,
                'raw_tags': stmt.excluded.raw_tags,
                'verified': stmt.excluded.verified,
                'last_updated': stmt.excluded.last_updated,
            },
        )
        await session.execute(upsert_stmt)
        await session.commit()

    return len(rows)


async def main() -> None:
    try:
        count = await seed_emergency_services()
        print(
            f'Seeded {count} emergency services across '
            'Chennai, Bengaluru, Mumbai, and Delhi.'
        )
    finally:
        await engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())
