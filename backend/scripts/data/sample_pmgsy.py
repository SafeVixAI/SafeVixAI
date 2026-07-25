# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""
sample_pmgsy.py
===============
Samples a representative subset of PMGSY roads from the full
pmgsy_roads.geojson (867K features) and writes a smaller GeoJSON
that import_official_road_sources.py can import without timing out.

Strategy: Take up to `max_per_state` roads per state so all 29 states
are represented, then cap the total at `total_limit`.

Usage:
    cd backend/
    python scripts/sample_pmgsy.py [--limit 5000] [--per-state 200]
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[1]
CHATBOT    = ROOT.parent / "chatbot_service" / "data"
SRC        = CHATBOT / "roads" / "pmgsy_roads.geojson"
OUT_DIR    = ROOT / "datasets" / "roads"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT        = OUT_DIR / "pmgsy_sampled.geojson"


def sample(total_limit: int = 5000, per_state: int = 200) -> None:
    print(f"Loading {SRC.name} ... (this takes ~30s for 867K features)")
    with SRC.open(encoding="utf-8") as fh:
        data = json.load(fh)

    all_features = data.get("features", [])
    print(f"Total features: {len(all_features):,}")

    buckets: dict[str, list] = defaultdict(list)
    for feat in all_features:
        state = feat.get("properties", {}).get("pmgsy_state", "Unknown")
        buckets[state].append(feat)

    selected = []
    for _state, feats in sorted(buckets.items()):
        chosen = feats[:per_state]
        selected.extend(chosen)
        if len(selected) >= total_limit:
            break

    selected = selected[:total_limit]
    print(f"Selected {len(selected):,} features from {len(buckets)} states")

    fc = {"type": "FeatureCollection", "features": selected}
    OUT.write_text(json.dumps(fc, ensure_ascii=False), encoding="utf-8")
    size_mb = OUT.stat().st_size / 1_048_576
    print(f"Written: {OUT.relative_to(ROOT)}  ({size_mb:.1f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit",     type=int, default=5000, help="Max total roads")
    parser.add_argument("--per-state", type=int, default=200,  help="Max roads per state")
    args = parser.parse_args()
    sample(args.limit, args.per_state)
    print("\nDone. Now update scripts/road_sources.json to use:")
    print("  datasets/roads/pmgsy_sampled.geojson")
