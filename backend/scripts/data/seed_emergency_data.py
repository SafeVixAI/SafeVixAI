# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

#!/usr/bin/env python3
"""
Seed Script: India Emergency Data via Overpass API
Generates blood banks, police stations, and fire stations for 25 cities.
Run: python scripts/seed_emergency_data.py

Output:
  datasets/emergency/blood_banks/india_blood_banks.json
  datasets/emergency/hospitals/india_hospitals_top25.json
  datasets/police/stations/india_police_stations.json
"""
import asyncio
import json
import sys
import time
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Top 25 India cities with bounding boxes [south, west, north, east]
CITIES = {
    "chennai":          [12.8, 80.1, 13.3, 80.4],
    "mumbai":           [18.8, 72.7, 19.3, 73.0],
    "delhi":            [28.4, 76.9, 28.9, 77.4],
    "bengaluru":        [12.8, 77.4, 13.2, 77.8],
    "hyderabad":        [17.2, 78.3, 17.6, 78.6],
    "kolkata":          [22.4, 88.2, 22.7, 88.5],
    "pune":             [18.4, 73.7, 18.6, 74.0],
    "ahmedabad":        [22.9, 72.4, 23.2, 72.7],
    "jaipur":           [26.8, 75.7, 27.0, 75.9],
    "lucknow":          [26.7, 80.8, 27.0, 81.1],
    "surat":            [21.1, 72.7, 21.3, 73.0],
    "nagpur":           [21.0, 78.9, 21.3, 79.2],
    "patna":            [25.5, 85.0, 25.7, 85.2],
    "indore":           [22.6, 75.7, 22.8, 75.9],
    "bhopal":           [23.1, 77.3, 23.3, 77.5],
    "coimbatore":       [10.9, 76.8, 11.1, 77.1],
    "visakhapatnam":    [17.6, 83.1, 17.8, 83.3],
    "kochi":            [9.9, 76.2, 10.1, 76.4],
    "vadodara":         [22.2, 73.1, 22.4, 73.3],
    "amritsar":         [31.6, 74.8, 31.7, 74.9],
    "ranchi":           [23.2, 85.2, 23.5, 85.4],
    "chandigarh":       [30.6, 76.7, 30.8, 76.9],
    "guwahati":         [26.1, 91.6, 26.2, 91.9],
    "bhubaneswar":      [20.2, 85.7, 20.4, 85.9],
    "thiruvananthapuram": [8.4, 76.8, 8.6, 77.0],
}


async def query_overpass(query: str, retries: int = 3) -> dict:
    """Execute Overpass query with retry across multiple endpoints."""
    headers = {
        "User-Agent": "SafeVixAI/2.0 Emergency Data Seeder (contact@safevixai.in)",
        "Accept": "application/json",
    }
    async with httpx.AsyncClient(timeout=60, headers=headers) as client:
        for _attempt in range(retries):
            for url in OVERPASS_URLS:
                try:
                    resp = await client.post(url, data={"data": query})
                    resp.raise_for_status()
                    return resp.json()
                except Exception as e:
                    print(f"  [WARN] {url} failed: {e}")
                    await asyncio.sleep(2)
    return {"elements": []}


def build_query(bbox: list, amenity_filter: str) -> str:
    s, w, n, e = bbox
    return f"""
[out:json][timeout:30];
(
  node[{amenity_filter}]({s},{w},{n},{e});
  way[{amenity_filter}]({s},{w},{n},{e});
);
out center tags;
""".strip()


def extract_elements(data: dict, city: str, category: str) -> list:
    items = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        items.append({
            "id": f"{city}-{el['id']}",
            "name": tags.get("name") or f"{category.title()} ({city})",
            "category": category,
            "city": city,
            "lat": float(lat),
            "lon": float(lon),
            "phone": tags.get("phone") or tags.get("contact:phone"),
            "address": ", ".join(filter(None, [
                tags.get("addr:housenumber"),
                tags.get("addr:street"),
                tags.get("addr:suburb"),
                tags.get("addr:city") or city.title(),
            ])) or None,
            "is_24hr": tags.get("opening_hours") == "24/7",
            "source": "overpass",
        })
    return items


async def seed_blood_banks():
    """Seed India blood banks from Overpass OSM data."""
    print("\n[BLOOD BANKS] Seeding blood banks...")
    all_items = []
    for city, bbox in CITIES.items():
        query = build_query(bbox, 'amenity="blood_bank"')
        data = await query_overpass(query)
        items = extract_elements(data, city, "blood_bank")
        all_items.extend(items)
        print(f"  {city}: {len(items)} blood banks")
        await asyncio.sleep(1)  # Rate limit

    out_path = Path(__file__).parents[2] / "datasets" / "emergency" / "blood_banks" / "india_blood_banks.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_items, f, indent=2)
    print(f"[OK] Saved {len(all_items)} blood banks -> {out_path}")


async def seed_police_stations():
    """Seed India police stations from Overpass OSM data."""
    print("\n[POLICE] Seeding police stations...")
    all_items = []
    for city, bbox in CITIES.items():
        query = build_query(bbox, 'amenity="police"')
        data = await query_overpass(query)
        items = extract_elements(data, city, "police")
        all_items.extend(items)
        print(f"  {city}: {len(items)} police stations")
        await asyncio.sleep(1)

    out_path = Path(__file__).parents[2] / "datasets" / "police" / "stations" / "india_police_stations.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_items, f, indent=2)
    print(f"[OK] Saved {len(all_items)} police stations -> {out_path}")


async def seed_fire_stations():
    """Seed India fire stations from Overpass OSM data."""
    print("\n[FIRE] Seeding fire stations...")
    all_items = []
    for city, bbox in CITIES.items():
        query = build_query(bbox, 'amenity="fire_station"')
        data = await query_overpass(query)
        items = extract_elements(data, city, "fire")
        all_items.extend(items)
        print(f"  {city}: {len(items)} fire stations")
        await asyncio.sleep(1)

    out_path = Path(__file__).parents[2] / "datasets" / "emergency" / "hospitals" / "india_fire_stations.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_items, f, indent=2)
    print(f"[OK] Saved {len(all_items)} fire stations -> {out_path}")


async def seed_hospitals():
    """Seed top-tier India hospitals with trauma/ICU flags."""
    print("\n[HOSPITALS] Seeding hospitals...")
    all_items = []
    for city, bbox in CITIES.items():
        query = build_query(bbox, 'amenity="hospital"')
        data = await query_overpass(query)
        items = extract_elements(data, city, "hospital")
        # Tag trauma centres and ICU hospitals
        for item in items:
            name_lower = item["name"].lower()
            item["has_trauma"] = "trauma" in name_lower or "aiims" in name_lower
            item["has_icu"] = "icu" in name_lower or "government" in name_lower
        all_items.extend(items)
        print(f"  {city}: {len(items)} hospitals")
        await asyncio.sleep(1)

    out_path = Path(__file__).parents[2] / "datasets" / "emergency" / "hospitals" / "india_hospitals_top25.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(all_items, f, indent=2)
    print(f"[OK] Saved {len(all_items)} hospitals -> {out_path}")


async def main():
    start = time.time()
    await seed_blood_banks()
    await seed_police_stations()
    await seed_fire_stations()
    await seed_hospitals()
    elapsed = time.time() - start
    print(f"\n[DONE] All seeding done in {elapsed:.1f}s")


if __name__ == "__main__":
    asyncio.run(main())
