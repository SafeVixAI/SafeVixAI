# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
"""Healthsites.io Hospital Seeder — ONE-TIME script.

Pulls hospital data from Healthsites.io API to supplement OSM Overpass data.
Inserts into the emergency_services table in Supabase/PostGIS.

Usage:
    HEALTHSITES_TOKEN=your_token python scripts/seed_healthsites.py

Sign up free: https://healthsites.io/
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "backend"))


HEALTHSITES_URL = "https://healthsites.io/api/v2/facilities/"


def fetch_all_facilities(token: str, country: str = "IND") -> list[dict]:
    """Fetch all Healthsites facilities for a country via paginated API requests.

    Args:
        token: Healthsites API token used for `Authorization: Token <token>`.
        country: ISO country code used to filter facilities (default: "IND").

    Returns:
        A list of facility dictionaries. Each dictionary contains:
        - name (str): Facility name.
        - category (str): Normalized category derived from amenity.
        - lat (float): Latitude from centroid coordinates.
        - lon (float): Longitude from centroid coordinates.
        - source (str): Constant source label ("healthsites.io").
        - uuid (str): Facility UUID from Healthsites.

    Side Effects:
        - Performs outbound HTTPS requests to the Healthsites API.
        - Iterates through paginated results until no `next` page exists.
        - Sleeps 1 second between pages for rate limiting.

    Raises:
        httpx.HTTPStatusError: If the API returns a non-success HTTP status.

    """
    facilities = []
    page = 1

    with httpx.Client(timeout=30.0) as client:
        while True:
            print(f"  Fetching page {page}...")
            response = client.get(
                HEALTHSITES_URL,
                params={"country": country, "page": page},
                headers={"Authorization": f"Token {token}"},
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                break

            for fac in results:
                name = fac.get("name", "").strip()
                amenity = fac.get("attributes", {}).get("amenity", "")
                lat = fac.get("centroid", {}).get("coordinates", [None, None])[1]
                lon = fac.get("centroid", {}).get("coordinates", [None, None])[0]

                if name and lat is not None and lon is not None:
                    facilities.append({
                        "name": name,
                        "category": _map_amenity(amenity),
                        "lat": lat,
                        "lon": lon,
                        "source": "healthsites.io",
                        "uuid": fac.get("uuid", ""),
                    })

            # Check for next page
            if not data.get("next"):
                break

            page += 1
            time.sleep(1)  # Rate limit

    return facilities


def _map_amenity(amenity: str) -> str:
    """Map Healthsites amenity type to our category schema."""
    amenity = amenity.lower()
    if "hospital" in amenity or "clinic" in amenity:
        return "hospital"
    if "pharmacy" in amenity:
        return "pharmacy"
    if "doctors" in amenity:
        return "hospital"
    return "hospital"  # Default


def _sql_literal(value: object) -> str:
    """Return a SQL literal for a Python value."""
    if value is None:
        return "NULL"
    if isinstance(value, float):
        import math
        if not math.isfinite(value):
            raise ValueError(f"Non-finite float value cannot be used as a SQL literal: {value!r}")
        return str(value)
    if isinstance(value, int):
        return str(value)
    text = str(value).replace("'", "''")
    return f"'{text}'"


def main() -> None:
    token = os.getenv("HEALTHSITES_TOKEN", "")
    if not token:
        print("❌ HEALTHSITES_TOKEN not set. Get a free token at https://healthsites.io/")
        print("   Usage: HEALTHSITES_TOKEN=your_token python scripts/seed_healthsites.py")
        sys.exit(1)

    print("🏥 Healthsites.io Hospital Seeder")
    print("=" * 50)
    print("Fetching facilities for India...")

    facilities = fetch_all_facilities(token)
    print(f"\n✅ Fetched {len(facilities)} facilities from Healthsites.io")

    if not facilities:
        print("No facilities found. Check your token.")
        sys.exit(1)

    # Output as SQL for manual review / import
    output_file_env = os.getenv("HEALTHSITES_OUTPUT_FILE", "").strip()
    if output_file_env:
        output_file = Path(output_file_env).expanduser().resolve()
    else:
        output_file = ROOT / "backend" / "data" / "healthsites_seed.sql"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("-- Healthsites.io hospital seed data\n")
        f.write("-- Generated by scripts/seed_healthsites.py\n\n")
        for fac in facilities:
            name_sql = _sql_literal(fac["name"])
            category_sql = _sql_literal(fac["category"])
            lon_sql = _sql_literal(fac["lon"])
            lat_sql = _sql_literal(fac["lat"])
            source_sql = _sql_literal("healthsites.io")
            f.write(
                f"INSERT INTO emergency_services (name, category, location, source) "
                f"VALUES ({name_sql}, {category_sql}, "
                f"ST_SetSRID(ST_MakePoint({lon_sql}, {lat_sql}), 4326), "
                f"{source_sql}) ON CONFLICT DO NOTHING;\n"
            )

    print(f"📁 SQL seed file written to: {output_file}")
    print(f"   Review and run: psql -d your_db -f {output_file}")


if __name__ == "__main__":
    main()
