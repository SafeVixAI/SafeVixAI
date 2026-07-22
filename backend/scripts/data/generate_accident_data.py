# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

"""
Enterprise Accident Data Pipeline
Generates:
  1. accidents_summary.json  -> frontend/public/ + backend/data/
  2. blackspot_seed.csv      -> backend/datasets/accidents/
from the 1M-row Kaggle India road accidents CSV.
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

# Windows-safe UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

try:
    import pandas as pd
except ImportError:
    sys.exit("pandas not installed. Run: pip install pandas")

# ── Paths ─────────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parents[3]  # IITM/ repo root
CSV_PATH = REPO_ROOT / "backend" / "datasets" / "accidents" / "kaggle" / "india_road_accident_coords.csv"
OUT_SUMMARY = REPO_ROOT / "frontend" / "public" / "accidents_summary.json"
OUT_SUMMARY_BACKEND = REPO_ROOT / "backend" / "data" / "accidents_summary.json"
OUT_BLACKSPOT = REPO_ROOT / "backend" / "datasets" / "accidents" / "blackspot_seed.csv"
OUT_BLACKSPOT_OFFLINE = REPO_ROOT / "frontend" / "public" / "offline-data" / "blackspot_seed.csv"

if not CSV_PATH.exists():
    sys.exit(f"CSV not found: {CSV_PATH}")

# ── Load ──────────────────────────────────────────────────────────────────────
print("Loading 1M accident records...")
df = pd.read_csv(CSV_PATH, low_memory=False)
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
print(f"Loaded {len(df):,} rows | columns: {list(df.columns[:10])}")

# ── Fix columns ───────────────────────────────────────────────────────────────
lat_col  = next((c for c in df.columns if "lat" in c), None)
lon_col  = next((c for c in df.columns if "lon" in c or "lng" in c), None)
sev_col  = next((c for c in df.columns if "severity" in c), None)
cas_col  = next((c for c in df.columns if "casual" in c), None)

print(f"lat={lat_col} lon={lon_col} severity={sev_col} casualties={cas_col}")

# coerce to numeric
for col in [lat_col, lon_col, sev_col, cas_col]:
    if col:
        df[col] = pd.to_numeric(df[col], errors="coerce")

# Drop rows with no GPS
df_geo = df.dropna(subset=[lat_col, lon_col]).copy()
print(f"Rows with GPS: {len(df_geo):,}")

# ── 1. National Summary JSON ──────────────────────────────────────────────────
total_accidents = len(df)
total_casualties = int(df[cas_col].sum()) if cas_col else 0

# Severity breakdown (1=Fatal, 2=Serious, 3=Slight — UK STATS19 encoding)
severity_map = {1: "fatal", 2: "serious", 3: "slight"}
severity_counts: dict = {}
if sev_col:
    for sev_val, label in severity_map.items():
        count = int((df[sev_col] == sev_val).sum())
        severity_counts[label] = count

# Day-of-week analysis
dow_col = next((c for c in df.columns if "day" in c and "week" in c), None)
day_names = {1:"Sunday",2:"Monday",3:"Tuesday",4:"Wednesday",5:"Thursday",6:"Friday",7:"Saturday"}
dow_stats: list = []
if dow_col:
    df[dow_col] = pd.to_numeric(df[dow_col], errors="coerce")
    dow = df.groupby(dow_col).size().sort_values(ascending=False)
    dow_stats = [{"day": day_names.get(int(k), str(k)), "accidents": int(v)} for k, v in dow.items()]

# Speed analysis
speed_col = next((c for c in df.columns if "speed" in c), None)
speed_stats: dict = {}
if speed_col:
    df[speed_col] = pd.to_numeric(df[speed_col], errors="coerce")
    speed_stats = {
        "mean_speed_limit": round(float(df[speed_col].mean()), 1),
        "high_speed_gt80": int((df[speed_col] > 80).sum()),
    }

summary = {
    "generated_at": "2026-04-27",
    "source": "Kaggle India Road Accidents Dataset (UK STATS19 encoding)",
    "total_accidents": total_accidents,
    "total_casualties": total_casualties,
    "accidents_with_gps": len(df_geo),
    "severity_breakdown": severity_counts,
    "accidents_by_day_of_week": dow_stats,
    "speed_analysis": speed_stats,
    "data_note": "Dataset uses UK STATS19 police-recorded format. Severity: 1=Fatal, 2=Serious, 3=Slight.",
}

OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
OUT_SUMMARY_BACKEND.parent.mkdir(parents=True, exist_ok=True)

with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
with open(OUT_SUMMARY_BACKEND, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"accidents_summary.json written ({OUT_SUMMARY.stat().st_size//1024} KB)")

# ── 2. Blackspot Seed CSV ─────────────────────────────────────────────────────
print("Generating GPS blackspot clusters (1km grid)...")

df_geo["lat_r"] = df_geo[lat_col].round(2)
df_geo["lon_r"] = df_geo[lon_col].round(2)

agg = {lat_col: "mean", lon_col: "mean", "lat_r": "count"}
if cas_col:
    agg[cas_col] = "sum"
if sev_col:
    agg[sev_col] = "mean"

hotspots = (
    df_geo.groupby(["lat_r", "lon_r"])
    .agg(
        accident_count=(lat_col, "count"),
        latitude=(lat_col, "mean"),
        longitude=(lon_col, "mean"),
        **({"total_casualties": (cas_col, "sum")} if cas_col else {}),
        **({"avg_severity": (sev_col, "mean")} if sev_col else {}),
    )
    .reset_index()
)

# Only keep clusters with at least 2 accidents (removes noise)
hotspots = hotspots[hotspots["accident_count"] >= 2].copy()

# Risk score = accident_count * (1 + casualties / 10)
if "total_casualties" in hotspots.columns:
    hotspots["risk_score"] = (
        hotspots["accident_count"] * (1 + hotspots["total_casualties"] / 10)
    ).round(2)
else:
    hotspots["risk_score"] = hotspots["accident_count"].astype(float)

hotspots = hotspots.sort_values("risk_score", ascending=False)

OUT_BLACKSPOT.parent.mkdir(parents=True, exist_ok=True)
OUT_BLACKSPOT_OFFLINE.parent.mkdir(parents=True, exist_ok=True)

hotspots.to_csv(OUT_BLACKSPOT, index=False)
hotspots.to_csv(OUT_BLACKSPOT_OFFLINE, index=False)

print(f"blackspot_seed.csv: {len(hotspots):,} clusters | top risk_score={hotspots['risk_score'].iloc[0]:.1f}")
print(f"Written to: {OUT_BLACKSPOT}")
print(f"Written to: {OUT_BLACKSPOT_OFFLINE}")
print("\nDONE - Enterprise accident data pipeline complete.")
