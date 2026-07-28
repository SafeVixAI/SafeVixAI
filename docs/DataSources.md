# SafeVixAI  Data Sources

## Overview

All data sources used in SafeVixAI are free and open. This document lists every data source, its URL, how to access it, and what it's used for.

---

## 1. PDFs  RAG Knowledge Base (Download Manually)

| Document | Source URL | Save As | Purpose |
|---|---|---|---|
 | Motor Vehicles Act 1988 | [indiacode.nic.in](https://www.indiacode.nic.in)  search "Motor Vehicles Act 1988" | `chatbot_service/data/legal/motor_vehicles_act_1988.pdf` | All base traffic law provisions + section numbers |
| MV Amendment Act 2019 | [morth.nic.in](https://morth.nic.in/motor-vehicles-amendment-act-2019) | `chatbot_service/data/legal/mv_amendment_act_2019.pdf` | Updated 2019 fine amounts (10x increase) |
| WHO Trauma Care Guidelines | [who.int](https://www.who.int)  search "emergency care systems for universal health coverage" | `chatbot_service/data/medical/who_trauma_care_guidelines.pdf` | First-aid protocols: bleeding, fractures, burns, CPR |
| WHO Global Road Safety Report 2023 | [who.int](https://www.who.int/publications/i/item/9789240086517) | `chatbot_service/data/legal/who_road_safety_2023.pdf` | Traffic laws for 100+ countries (speed limits, BAC limits, helmet laws) |
| State Amendment PDFs | Each state transport department website | `chatbot_service/data/legal/state_amendments/[state].pdf` | State-level fine overrides and additional rules |

---

## 2. APIs  Live Data (No API Key Required)

### OpenStreetMap Overpass API
- **URL**: `https://overpass-api.de/api/interpreter`
- **Authentication**: None (fair use)
- **Rate limit**: ~1 request/second
- **Use in SafeVixAI**: Live queries for emergency service locations worldwide
- **Data**: Hospitals, police stations, ambulance stations, petrol pumps, pharmacies, ATMs

```
# Example: find hospitals within 5km of Chennai
[out:json][timeout:25];
(
  node[amenity~"hospital|clinic|doctors"](around:5000,13.0827,80.2707);
  way[amenity~"hospital|clinic|doctors"](around:5000,13.0827,80.2707);
);
out body center;
```

### Nominatim Geocoder
- **URL**: `https://nominatim.openstreetmap.org`
- **Authentication**: None (User-Agent header required)
- **Rate limit**: 1 request/second strictly enforced
- **Use in SafeVixAI**: GPS coordinates  city/state name, address  coordinates

```
# Required header: User-Agent: SafeVixAI/1.0 (Project@rbg.iitm.ac.in)
# Reverse: GET /reverse?lat=13.0827&lon=80.2707&format=json&addressdetails=1
# Forward: GET /search?q=Apollo+Hospital+Chennai&format=json&limit=1
```

### Groq LLM API
- **URL**: `https://api.groq.com/openai/v1`
- **Authentication**: API key (gsk_...) from [console.groq.com](https://console.groq.com)
- **Rate limit**: 6,000 tokens/minute free tier
- **Use in SafeVixAI**: Online AI chatbot — llama-3.1-8b-instant model

### Overpass Turbo (Testing Only)
- **URL**: [overpass-turbo.eu](https://overpass-turbo.eu)
- **Use**: Test Overpass queries before implementing in code

---

## 3. APIs  Government Open Data (API Key Required)

### data.gov.in
- **URL**: [api.data.gov.in](https://api.data.gov.in)
- **Authentication**: Free API key after registration at [data.gov.in](https://data.gov.in)
- **Use in SafeVixAI**: NHAI road project data (contractor names, budgets, construction dates)
- **Key datasets**:
  - NHAI National Highway Projects
  - Accident data by state and district
  - Government hospital registry

### PMGSY OMMAS
- **URL**: [ommas.nic.in](https://ommas.nic.in)
- **Authentication**: Public portal, no API  scrape or use exported data
- **Use in SafeVixAI**: Rural road infrastructure data (contractor, exec engineer, budget)

### National Health Facility Registry
- **URL**: [healthfacilities.in](https://healthfacilities.in)
- **Authentication**: Public API available
- **Use in SafeVixAI**: Government hospital locations, contact numbers, specializations

---

## 4. OSM Seed Data  25 Indian Cities

Seeded from Overpass API by `data/seed_emergency.py`. Stored in PostgreSQL + exported as GeoJSON.

| City | State | Lat | Lon |
|---|---|---|---|
| Chennai | Tamil Nadu | 13.0827 | 80.2707 |
| Coimbatore | Tamil Nadu | 11.0168 | 76.9558 |
| Madurai | Tamil Nadu | 9.9252 | 78.1198 |
| Thiruvananthapuram | Kerala | 8.5241 | 76.9366 |
| Kochi | Kerala | 9.9312 | 76.2673 |
| Bengaluru | Karnataka | 12.9716 | 77.5946 |
| Mumbai | Maharashtra | 19.0760 | 72.8777 |
| Pune | Maharashtra | 18.5204 | 73.8567 |
| Nagpur | Maharashtra | 21.1458 | 79.0882 |
| Hyderabad | Telangana | 17.3850 | 78.4867 |
| Delhi | Delhi | 28.6139 | 77.2090 |
| Jaipur | Rajasthan | 26.9124 | 75.7873 |
| Ahmedabad | Gujarat | 23.0225 | 72.5714 |
| Surat | Gujarat | 21.1702 | 72.8311 |
| Vadodara | Gujarat | 22.3072 | 73.1812 |
| Kolkata | West Bengal | 22.5726 | 88.3639 |
| Patna | Bihar | 25.5941 | 85.1376 |
| Bhopal | Madhya Pradesh | 23.2599 | 77.4126 |
| Indore | Madhya Pradesh | 22.7196 | 75.8577 |
| Lucknow | Uttar Pradesh | 26.8467 | 80.9462 |
| Agra | Uttar Pradesh | 27.1767 | 78.0081 |
| Varanasi | Uttar Pradesh | 25.3176 | 82.9739 |
| Chandigarh | Punjab/Haryana | 30.7333 | 76.7794 |
| Visakhapatnam | Andhra Pradesh | 17.6868 | 83.2185 |
| Bhubaneswar | Odisha | 20.2961 | 85.8245 |

---

## 5. Traffic Violations Data  violations_seed.csv

Generated from official MV Amendment Act 2019 gazette notification. The CSV has these columns:

```
violation_code, section, description_en, base_fine_inr, repeat_fine_inr,
vehicle_type, imprisonment, dl_points
```

All 22+ sections from MVA 1988/2019 are pre-populated. See `docs/Database.md` for the complete violations reference table.

---

## 6. State Override Data  state_overrides.csv

State-specific fine amounts that override national MVA fines. Research from official state transport department notifications.

```
violation_code, state_code, override_fine, authority, effective_date
```

States covered: TN (Tamil Nadu), KA (Karnataka), MH (Maharashtra), DL (Delhi), AP (Andhra Pradesh), TS (Telangana), KL (Kerala), RJ (Rajasthan)

**Verify all amounts** against official state gazette notifications before using in production.

---

## 7. WebLLM Model Weights  CDN

| Model | HF Repo | Size | Download |
|---|---|---|---|
| Phi-3 Mini 4-bit | `microsoft/Phi-3-mini-4k-instruct` | ~2.2GB | Auto via WebLLM |
| Gemma 2B 4-bit | `google/gemma-2b-it` | ~1.4GB | Auto via WebLLM |
| LocalHashEmbeddingFunction (browser) | `Xenova/LocalHashEmbeddingFunction` | ~25MB | Auto via Transformers.js |
| YOLOv8n (browser) | `Xenova/yolov8n` | ~15MB | Auto via Transformers.js |

WebLLM fetches directly from Hugging Face CDN and caches in browser Cache Storage. Users do not need a Hugging Face account.

---

## 8. Government Portals (Deep Links Only  No Data Pull)

| Portal | URL | Used For |
|---|---|---|
| eChallan Payment | echallan.parivahan.gov.in | Link to pay fines after challan lookup |
| mParivahan | parivahan.gov.in | Vehicle RC / DL verification |
| VAHAN | vahan.parivahan.gov.in | Vehicle registration database |
| SARATHI | sarathi.parivahan.gov.in | Driving licence database |
| NHAI Complaint | nhai.gov.in/complaint | Route NH complaints here |
| CPGRAMS | pgportal.gov.in | Universal government complaint portal |
| PMGSY OMMAS | ommas.nic.in | Rural road complaint portal |
| NHAI Helpline | 1033 | Highway emergency tel: link |

---

*Document version: 1.0 | AI-powered road safety platform*
