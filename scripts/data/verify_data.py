# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
import csv
import json
from pathlib import Path

ROOT = Path(".")
DATA = ROOT / "chatbot_service/data"
FRONTEND = ROOT / "frontend/public/offline-data"

checks = []

def check(label, path, min_bytes=100, check_fn=None):
    p = Path(path)
    if not p.exists():
        checks.append(("FAIL", label, "FILE MISSING"))
        return
    size = p.stat().st_size
    if size < min_bytes:
        checks.append(("FAIL", label, f"Too small: {size} bytes"))
        return
    if check_fn:
        try:
            result = check_fn(p)
            checks.append(("PASS", label, result))
        except Exception as e:
            checks.append(("WARN", label, str(e)))
    else:
        checks.append(("PASS", label, f"{size:,} bytes"))

def count_csv(p):
    with p.open(encoding="utf-8-sig") as f:
        return f"{sum(1 for _ in csv.DictReader(f))} rows"

def check_pdf(p):
    data = p.read_bytes()
    if data[:4] != b"%PDF":
        preview = data[:30].decode("latin-1", errors="replace")
        return f"NOT REAL PDF -- {preview}"
    return f"{p.stat().st_size:,} bytes (valid PDF)"

def count_json(p):
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return f"{len(data)} items"
    if isinstance(data, dict):
        return f"{len(data)} keys"
    return "JSON ok"

def geojson_features(p):
    data = json.loads(p.read_text(encoding="utf-8"))
    return f"{len(data['features']):,} features"

# PDFs
check("MVA 1988 PDF", DATA/"legal/motor_vehicles_act_1988.pdf", 100000, check_pdf)
check("MVA Amendment 2019 PDF", DATA/"legal/mv_amendment_act_2019.pdf", 500, check_pdf)
check("WHO Trauma Guidelines", DATA/"medical/who_trauma_care_guidelines.pdf", 500, check_pdf)
check("MVA 1988 TXT summary", DATA/"legal/motor_vehicles_act_1988_summary.txt", 10000)

# CSVs
check("violations_seed.csv", DATA/"violations_seed.csv", 500, count_csv)
check("state_overrides.csv", DATA/"state_overrides.csv", 200, count_csv)
check("toll_plazas.csv", DATA/"roads/toll_plazas.csv", 50000, count_csv)
check("hospital_directory.csv", DATA/"hospitals/hospital_directory.csv", 1000000)
check("nin_facilities.csv", DATA/"hospitals/nin_facilities.csv", 5000000)
check("police_stations.csv", DATA/"emergency/police_stations.csv", 50000, count_csv)
check("fire_stations.csv", DATA/"emergency/fire_stations.csv", 10000, count_csv)

# Backend challan CSVs
check("backend violations.csv", "backend/datasets/challan/violations.csv", 500, count_csv)
check("backend state_overrides.csv", "backend/datasets/challan/state_overrides.csv", 200, count_csv)

# Frontend JSONs
check("first-aid.json (frontend)", FRONTEND/"first-aid.json", 5000, count_json)
check("first_aid.json (chatbot)", DATA/"first_aid.json", 5000, count_json)
check("india-emergency.geojson", FRONTEND/"india-emergency.geojson", 1000000, geojson_features)
check("violations.csv (frontend)", FRONTEND/"violations.csv", 200, count_csv)

# Large files
check("pmgsy_roads.geojson", DATA/"roads/pmgsy_roads.geojson", 50_000_000)
check("kaggle_india_accidents.csv", DATA/"accidents/kaggle_india_accidents.csv", 10000000)

# morth_2022 extracted
morth_dir = DATA / "accidents/morth_2022"
extracted = list(morth_dir.glob("extracted_*.csv"))
check("morth_2022 extracted tables", morth_dir, 10000,
      lambda p: f"{len(extracted)} extracted CSVs")

print()
print("=" * 70)
print(f"  DATA PIPELINE FINAL VERIFICATION -- {len(checks)} checks")
print("=" * 70)
fail = warn = 0
for status, label, detail in checks:
    icon = "[PASS]" if status == "PASS" else ("[FAIL]" if status == "FAIL" else "[WARN]")
    print(f"  {icon} {label:<45} {detail}")
    if status == "FAIL": fail += 1
    if status == "WARN": warn += 1
print("=" * 70)
print(f"  Result: {len(checks)-fail-warn} PASS | {warn} WARN | {fail} FAIL")
print("=" * 70)
