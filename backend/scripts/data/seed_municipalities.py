# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Seed municipalities from JSON — standalone script (no DB required for dry-run)."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))


async def seed_municipalities(dry_run: bool = False) -> None:
    """Load municipalities_seed.json into the municipalities table."""
    data_path = Path(__file__).resolve().parents[2] / 'data' / 'civic_intel' / 'municipalities_seed.json'

    with open(data_path, encoding='utf-8') as f:
        municipalities = json.load(f)

    print(f'[Seed] Loaded {len(municipalities)} municipalities from {data_path.name}')

    if dry_run:
        # Preview only
        for m in municipalities[:5]:
            print(f"  → {m['short_name']:8s} | {m['name']:50s} | {m['city']:20s} | {m['state_code']}")
        print(f'  ... and {len(municipalities) - 5} more')
        return

    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from core.database import AsyncSessionLocal
    from models.municipality import Municipality

    async with AsyncSessionLocal() as db:
        inserted, updated = 0, 0
        for m in municipalities:
            stmt = pg_insert(Municipality).values(**m)
            stmt = stmt.on_conflict_do_update(
                index_elements=['slug'],
                set_={k: stmt.excluded.__getattr__(k) for k in m if k != 'slug'},
            )
            result = await db.execute(stmt)
            if result.rowcount > 0:
                inserted += 1
            else:
                updated += 1

        await db.commit()
        print(f'[Seed] Done: {inserted} inserted, {updated} updated')


if __name__ == '__main__':
    dry = '--dry-run' in sys.argv
    asyncio.run(seed_municipalities(dry_run=dry))
