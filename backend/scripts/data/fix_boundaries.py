# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""Download all 36 state district boundary GeoJSONs from udit-001/india-maps-data."""
import json
import time
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parents[2] / 'data' / 'civic_intel' / 'boundaries'
OUT.mkdir(parents=True, exist_ok=True)

BASE = 'https://raw.githubusercontent.com/udit-001/india-maps-data/main/geojson/states'

# All 36 states/UTs — filenames use hyphens
STATES = {
    'TN': 'tamil-nadu',
    'AP': 'andhra-pradesh',
    'UP': 'uttar-pradesh',
    'WB': 'west-bengal',
    'BR': 'bihar',
    'MP': 'madhya-pradesh',
    'OD': 'odisha',
    'JH': 'jharkhand',
    'AS': 'assam',
    'PB': 'punjab',
    'CG': 'chhattisgarh',
    'HR': 'haryana',
    'UK': 'uttarakhand',
    'HP': 'himachal-pradesh',
    'GA': 'goa',
    'MN': 'manipur',
    'ML': 'meghalaya',
    'MZ': 'mizoram',
    'NL': 'nagaland',
    'SK': 'sikkim',
    'TR': 'tripura',
    'AR': 'arunachal-pradesh',
    'JK': 'jammu-and-kashmir',
    'LA': 'ladakh',
    'CH': 'chandigarh',
    'PY': 'puducherry',
    'AN': 'andaman-and-nicobar-islands',
    'LD': 'lakshadweep',
    'DD': 'dnh-and-dd',
}

summary = {}
with httpx.Client(follow_redirects=True) as c:
    for code, slug in sorted(STATES.items()):
        outpath = OUT / f'{code.lower()}_districts.geojson'
        if outpath.exists() and outpath.stat().st_size > 100:
            data = json.loads(outpath.read_text(encoding='utf-8'))
            feats = len(data.get('features', []))
            print(f"SKIP {code}: already exists ({feats} features)")
            summary[code] = feats
            continue

        url = f'{BASE}/{slug}.geojson'
        try:
            r = c.get(url, timeout=60)
            if r.status_code == 200:
                data = r.json()
                feats = len(data.get('features', []))
                outpath.write_text(json.dumps(data), encoding='utf-8')
                kb = outpath.stat().st_size / 1024
                print(f"OK   {code}: {feats} features, {kb:.1f} KB")
                summary[code] = feats
            else:
                print(f"FAIL {code}: HTTP {r.status_code}")
                summary[code] = 0
        except Exception as e:
            print(f"ERR  {code}: {e}")
            summary[code] = 0
        time.sleep(0.3)

total = sum(summary.values())
print(f"\nTotal: {len(summary)} states, {total} district features")
