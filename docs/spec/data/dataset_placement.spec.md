# Dataset Placement

This file is the project-wide placement guide for every dataset, legal corpus file, and offline data asset mentioned in the SafeVixAI data and chatbot documents.

Use this file when downloading or copying resources into the repo.

## Scope

This guide covers placement for:
- backend import datasets (`backend/data/`)
- chatbot RAG/legal corpus files (`chatbot_service/data/`)
- frontend offline static data bundles (`frontend/public/offline-data/`)
- dataset manifests used for imports

This guide does not cover:
- secret keys or `.env` values
- model training datasets stored outside the repo
- dashboard-only benchmark/reference apps

## Placement Rules

- Put government and importable CSV/GeoJSON/JSON assets under `backend/data/` or `chatbot_service/data/`.
- Put chatbot legal/RAG PDFs and vectorstore source files under `chatbot_service/data/legal/` and `chatbot_service/data/medical/`.
- Put browser-consumed offline bundles under `frontend/public/offline-data/`.
- Keep very large raw training datasets outside git unless we explicitly decide otherwise.
- Prefer the suggested filenames below so import scripts and future docs stay consistent.

## 1. Backend Data Root

Base path: `backend/data/`

### 1.1 Emergency Services

| Dataset | Put it here | Suggested filename |
|---|---|---|
| National Hospital Directory with Geo Code | `chatbot_service/data/hospitals/` | `hospital_directory.csv` |
| Blood Bank Directory National Health Portal | `chatbot_service/data/hospitals/` | `blood_bank_directory.csv` |
| Number of Sub-Centres, PHCs and CHCs | `chatbot_service/data/hospitals/` | `phc_chc_counts_rural_urban.csv` |
| State-wise Number of PHCs/CHCs functioning Rural Urban | `chatbot_service/data/hospitals/` | `phc_chc_counts_rural_urban.csv` |
| NHM health facilities export | `chatbot_service/data/hospitals/` | `health_facilities_functioning_2005_to_2012.csv` |
| Ambulance stations | `chatbot_service/data/emergency/` | `ambulance_stations.csv` |
| Fire stations | `chatbot_service/data/emergency/` | `fire_stations.csv` |
| Police stations | `chatbot_service/data/emergency/` | `police_stations.csv` |
| TAEI Trauma centres | `chatbot_service/data/hospitals/` | `taei_trauma_centres.csv` |

### 1.2 Accident and Risk Datasets

| Dataset | Put it here | Suggested filename |
|---|---|---|
| Road Accidents in India 2022 | `chatbot_service/data/accidents/` | `road_accidents_india_2022.csv` |
| Road Accidents in India 2021 | `chatbot_service/data/accidents/` | `road_accidents_india_2021.csv` |
| Road Accidents in India 2020 | `chatbot_service/data/accidents/` | `road_accidents_india_2020.csv` |
| Road Accidents in India 2019 | `chatbot_service/data/accidents/` | `road_accidents_india_2019.csv` |
| State/UT/City-wise Traffic Accidents Cases Injured Died 2022 | `chatbot_service/data/accidents/` | `traffic_accidents_cases_injured_died_2022.csv` |
| Accidental Deaths and Suicides in India ADSI 2022 | `chatbot_service/data/accidents/` | `adsi_2022.csv` |
| MoRTH accidents by vehicle type 2012-2016 | `chatbot_service/data/accidents/` | `morth_vehicle_type_2012_2016.csv` |
| MoRTH accidents by road features 2014-2016 | `chatbot_service/data/accidents/` | `morth_road_features_2014_2016.csv` |
| Persons injured 2011-2014 | `chatbot_service/data/accidents/` | `morth_persons_injured_2011_2014.csv` |
| India road accident dataset with coordinates | `chatbot_service/data/accidents/` | `india_road_accident_coords.csv` |
| Road accident severity dataset | `chatbot_service/data/accidents/` | `road_accident_severity.csv` |
| Road accidents India (Manu Gupta) | `chatbot_service/data/accidents/_raw_manugupta/` | `only_road_accidents_data_month2.csv` |
| Crime Review India 2025 | `chatbot_service/data/accidents/` | `crime_review_india_2025.csv` |

### 1.3 Road Infrastructure and RoadWatch Sources

| Dataset | Put it here | Suggested filename |
|---|---|---|
| PMGSY Rural Roads export (single file) | `chatbot_service/data/roads/` | `pmgsy_roads.geojson` |
| National Highway Length state-wise | `chatbot_service/data/roads/` | `national_highways.csv` |
| Basic Road Statistics of India | `chatbot_service/data/roads/` | `basic_road_statistics_india.pdf` |
| State road data (construction length) | `chatbot_service/data/roads/` | `state_road_data_c3_2021_2024.csv` |
| District boundaries GeoJSON | `backend/data/civic_intel/boundaries/` | `<state_code>_districts.geojson` |
| NHAI Toll Plazas India | `chatbot_service/data/roads/` | `toll_plazas.csv` |
| City road network exports | `backend/data/civic_intel/road_network/` | `<city>_roads.csv` |
| OSM city features (CCTV, signals, bus stops, etc.) | `backend/data/civic_intel/osm_features/` | `<city>_<feature>.csv` |
| District boundaries metadata | `chatbot_service/data/boundaries/` | `india_districts-metadata-*.csv` |
| State boundaries metadata | `chatbot_service/data/boundaries/` | `india_states-metadata-*.csv` |

### 1.4 Police and Authority Routing Datasets

| Dataset | Put it here | Suggested filename |
|---|---|---|
| List of Police Stations India | `chatbot_service/data/emergency/` | `police_stations.csv` |
| District-wise Crime Statistics NCRB | `backend/data/civic_intel/datagov/` | `police_stations_by_state.csv` |
| State police contacts export | `chatbot_service/data/emergency/` | `police_stations.csv` |

### 1.5 Legal and Policy Corpora

| Dataset / file | Put it here | Suggested filename |
|---|---|---|
| Motor Vehicles Act 1988 PDF | `chatbot_service/data/legal/` | `motor_vehicles_act_1988.pdf` |
| MV Amendment Act 2019 PDF | `chatbot_service/data/legal/` | `mv_amendment_act_2019.pdf` |
| WHO Trauma Care Guidelines PDF | `chatbot_service/data/medical/` | `who_trauma_care_guidelines.pdf` |
| WHO Global Road Safety Report 2023 PDF | `chatbot_service/data/legal/` | `who_road_safety_indicators_ind.csv` |
| State amendment PDFs | `chatbot_service/data/legal/state_amendments/` | `<state>.pdf` |
| Indian Kanoon legal judgments | `chatbot_service/data/legal/indian_kanoon/` | `<case_name>.pdf` |
| Indian Kanoon act sections | `chatbot_service/data/legal/indian_kanoon/` | `indian_kanoon_act_sections.csv` |
| Indian Kanoon case citations | `chatbot_service/data/legal/indian_kanoon/` | `indian_kanoon_case_citations.csv` |

### 1.6 Dataset Manifests and Import Configs

| File | Put it here | Suggested filename |
|---|---|---|
| data.gov.in source manifest | `backend/data/civic_intel/` | `datagov_resources.json` |
| import run manifest / batch notes | `backend/data/` | `road_sources.example.json` |
| official road source manifest | `backend/data/civic_intel/` | `road_categories.json` |

### 1.7 Civil Intelligence / data.gov.in Datasets (Backend)

| Dataset | Put it here | Suggested filename |
|---|---|---|
| Road accidents by state | `backend/data/civic_intel/datagov/` | `road_accidents_by_state.csv` |
| Road accidents cause-wise | `backend/data/civic_intel/datagov/` | `road_accidents_cause_wise.csv` |
| Road length by surface type | `backend/data/civic_intel/datagov/` | `road_length_by_surface.csv` |
| Registered vehicles | `backend/data/civic_intel/datagov/` | `registered_vehicles.csv` |
| National highways length | `backend/data/civic_intel/datagov/` | `national_highways_length.csv` |
| Traffic violations | `backend/data/civic_intel/datagov/` | `traffic_violations.csv` |
| Smart city projects | `backend/data/civic_intel/datagov/` | `smart_city_projects.csv` |

## 2. Chatbot Service Data Root

Base path: `chatbot_service/data/`

These files are for RAG, legal reasoning, and chatbot-side retrieval.

| Dataset / file | Put it here | Suggested filename |
|---|---|---|
| Motor Vehicles Act 1988 PDF | `chatbot_service/data/legal/` | `motor_vehicles_act_1988.pdf` |
| MV Amendment Act 2019 PDF | `chatbot_service/data/legal/` | `mv_amendment_act_2019.pdf` |
| WHO Trauma Care Guidelines PDF | `chatbot_service/data/medical/` | `who_trauma_care_guidelines.pdf` |
| Offline first-aid JSON corpus | `chatbot_service/data/` | `first_aid.json` |
| Emergency numbers JSON | `chatbot_service/data/` | `emergency_numbers.json` |
| State amendment PDFs | `chatbot_service/data/legal/state_amendments/` | `<state>.pdf` |
| Indian Kanoon legal judgments | `chatbot_service/data/legal/indian_kanoon/` | `<case_name>.pdf` |
| Indian Kanoon act sections | `chatbot_service/data/legal/indian_kanoon/` | `indian_kanoon_act_sections.csv` |
| Indian Kanoon case citations | `chatbot_service/data/legal/indian_kanoon/` | `indian_kanoon_case_citations.csv` |
| Chroma persistence files (committed) | `chatbot_service/data/chroma_db/` | generated files |
| Violation rule definitions | `chatbot_service/data/` | `violations_seed.csv` |
| State override rules | `chatbot_service/data/` | `state_overrides.csv` |
| Vectorstore build script | `chatbot_service/data/` | `build_vectorstore.py` |
| Hospital directories | `chatbot_service/data/hospitals/` | `hospital_directory.csv` |
| Blood bank directory | `chatbot_service/data/hospitals/` | `blood_bank_directory.csv` |
| PHC/CHC counts | `chatbot_service/data/hospitals/` | `phc_chc_counts_rural_urban.csv` |
| Trauma centres | `chatbot_service/data/hospitals/` | `taei_trauma_centres.csv` |
| Rural health village coverage | `chatbot_service/data/hospitals/` | `rural_health_villages_coverage_2005.csv` |
| Hospital beds by institution type | `chatbot_service/data/hospitals/` | `hospital_beds_by_institution_type.csv` |
| NIN facilities | `chatbot_service/data/hospitals/` | `nin_facilities.csv` |
| Police stations | `chatbot_service/data/emergency/` | `police_stations.csv` |
| Fire stations | `chatbot_service/data/emergency/` | `fire_stations.csv` |
| Ambulance stations | `chatbot_service/data/emergency/` | `ambulance_stations.csv` |
| PMGSY roads | `chatbot_service/data/roads/` | `pmgsy_roads.geojson` |
| National highways | `chatbot_service/data/roads/` | `national_highways.csv` |
| Toll plazas | `chatbot_service/data/roads/` | `toll_plazas.csv` |
| State road length/works data | `chatbot_service/data/roads/` | `state_road_*.csv` |
| District road length | `chatbot_service/data/roads/` | `district_road_length_completed_2019_2023.csv` |
| Accident data | `chatbot_service/data/accidents/` | various |

Do not manually rename the generated Chroma files unless we also update the vectorstore code.

## 3. Frontend Offline Data Root

Base path: `frontend/public/offline-data/`

These files are meant to be served directly to the browser/PWA.

| Dataset / file | Put it here | Suggested filename |
|---|---|---|
| Offline first-aid reference bundle | `frontend/public/offline-data/` | `first-aid.json` |
| Offline emergency services GeoJSON | `frontend/public/offline-data/` | `india-emergency.geojson` |
| Compressed emergency GeoJSON | `frontend/public/offline-data/` | `india-emergency.geojson.gz` |
| Violations rules CSV | `frontend/public/offline-data/` | `violations.csv` |
| State override CSV | `frontend/public/offline-data/` | `state_overrides.csv` |
| National highway blackspots | `frontend/public/offline-data/` | `nh_blackspots.csv` |
| Blackspot seed data | `frontend/public/offline-data/` | `blackspot_seed.csv` |
| Accidents summary | `frontend/public/offline-data/` | `accidents_summary.json` |
| Civic features summary | `frontend/public/offline-data/` | `civic_features_summary.json` |
| Municipalities bundle | `frontend/public/offline-data/` | `municipalities_bundle.json` |
| City offline service bundles | `frontend/public/offline-data/` | `<city>.json` |
| City-specific bundles (subdir) | `frontend/public/offline-data/city-bundles/` | `<city>.json` |
| Translation packs | `frontend/public/offline-data/translations/` | `<lang>.json` |

## 4. ChromaDB — Two Locations

| Instance | Path | Git status | Rebuild |
|---|---|---|---|
| Chatbot service (primary) | `chatbot_service/data/chroma_db/` | **Committed** — needed for Render cold-starts | `python data/build_vectorstore.py` from `chatbot_service/` |
| Backend (secondary) | `backend/data/chroma_db/` | `.gitignored` — rebuild locally | `python scripts/data/build_backend_vectorstore.py` or equivalent |

## 5. Keep Outside the Repo by Default

These datasets are useful, but large enough that we should keep them outside normal git tracking unless we explicitly decide to vendor them.

| Dataset | Recommended local storage |
|---|---|
| Potholes YOLOv8 (Anggadwi) | `C:/datasets/potholes/anggadwi_yolov8/` |
| Pothole dataset (Sachin Patel) | `C:/datasets/potholes/sachin_patel/` |
| Pothole dataset (Andrew) | `C:/datasets/potholes/andrew_pascal_voc/` |
| Road Damage Dataset 2025 | `C:/datasets/road_damage_2025/` |
| Potholes + Cracks + Manholes | `C:/datasets/potholes_cracks_manholes/` |
| BhasaAnuvaad speech corpus | `C:/datasets/bhasaanuvaad/` |

## 6. Recommended Download Order

If we are collecting data in phases, use this order:

1. `chatbot_service/data/hospitals/hospital_directory.csv`
2. `chatbot_service/data/hospitals/blood_bank_directory.csv`
3. `chatbot_service/data/emergency/police_stations.csv`
4. `chatbot_service/data/emergency/ambulance_stations.csv`
5. `chatbot_service/data/emergency/fire_stations.csv`
6. `chatbot_service/data/roads/pmgsy_roads.geojson`
7. `chatbot_service/data/legal/motor_vehicles_act_1988.pdf`
8. `chatbot_service/data/legal/mv_amendment_act_2019.pdf`
9. `chatbot_service/data/legal/indian_kanoon/<case_name>.pdf`
10. `chatbot_service/data/medical/who_trauma_care_guidelines.pdf`
11. `frontend/public/offline-data/india-emergency.geojson`
12. `frontend/public/offline-data/city-bundles/<city>.json`
13. `backend/data/civic_intel/boundaries/<state_code>_districts.geojson`
14. `chatbot_service/data/chroma_db/` — run `build_vectorstore.py`
15. `frontend/public/offline-data/translations/<lang>.json`

## 7. Naming and Hygiene Rules

- Use lowercase filenames with underscores where possible.
- Prefer `.csv`, `.geojson`, `.json`, or `.pdf` as downloaded formats unless the source forces another format.
- If a source provides ZIP files, keep the original ZIP only temporarily, then extract and place the final data file in the correct target folder.
- Do not put API keys or tokens in these folders.
- Do not commit huge raw ML training datasets to the repo.

## 8. If a Dataset Does Not Match Cleanly

If you download a file and it does not fit one of the exact placements above:
- place it in the nearest matching category folder first
- keep the original source name in a side note or manifest
- then we can normalize it in an import manifest later

When in doubt, prefer category correctness over perfect filename matching.
