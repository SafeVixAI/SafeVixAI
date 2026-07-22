# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import asyncio
import os

import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def check():
    url = os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)

    # Check tables
    tables = await conn.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"
    )
    print('Tables in Supabase:')
    for t in tables:
        print(' -', t['tablename'])

    # Check row counts
    for table in ['emergency_services', 'road_infrastructure', 'road_issues']:
        try:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            print(f'  {table}: {count} rows')
        except Exception as e:
            print(f'  {table}: NOT FOUND - {e}')

    await conn.close()

asyncio.run(check())
