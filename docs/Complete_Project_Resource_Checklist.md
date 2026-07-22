# SafeVixAI Complete Project Resource Checklist

Generated from:
- [SafeVixAI_Complete_Resources_main.docx](C:/Hackathons/IITM/SafeVixAI_Complete_Resources_main.docx)
- [SafeVixAI_Chatbot_Impl_Plan.txt](C:/Hackathons/IITM/SafeVixAI_Chatbot_Impl_Plan.txt)
- [SafeVixAI_Chatbot_Guide.txt](C:/Hackathons/IITM/SafeVixAI_Chatbot_Guide.txt)
- [doc_text.txt](C:/Hackathons/IITM/doc_text.txt)

Last updated: 2026-06-09 — Brought in sync with actual repo state. All 25 features complete.

This file is the single source of truth for:
- what you need to collect
- where to get it
- where it belongs in the repo
- which env variable or file it maps to
- whether the current repo already uses it
- which future runtime/service/file assets the source documents still expect

Important notes:
- Do not commit secrets into git.
- Keep large datasets outside normal source control. Suggested local folder: `SafeVixAI/backend/datasets/`.
- Chatbot rows point to `chatbot_service/.env`.

## Status legend

| Status | Meaning |
|---|---|
| `Wired now` | Current code already references this item. |
| `Needs value` | Current code expects it, but you must add the real value. |
| `Needs download` | You must manually download the file or dataset. |
| `Partially wired` | Some scaffolding exists, but import/provider integration is not complete yet. |
| `Future phase` | Recommended by the document, but not implemented in the current repo yet. |
| `Reference only` | Mentioned as a benchmark, portal, or workflow aid; no repo download is required. |
| `Skip` | The document explicitly says this is not worth using as the main path. |
| `Complete` | Fully implemented and wired. |

## 1. Core accounts, hosting, and deployment services

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Supabase project | https://supabase.com | Dashboard account only | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Wired now | Critical |
| Upstash Redis | https://upstash.com | Dashboard account only | `REDIS_URL` | Wired now | Critical |
| Render backend hosting | https://render.com | Dashboard account only | N/A | Wired now | High |
| Vercel frontend hosting | https://vercel.com | Dashboard account only | N/A | Wired now | High |
| data.gov.in account | https://data.gov.in | Dashboard account only | `DATA_GOV_API_KEY` | Partially wired | Critical |
| AI Kosh account | https://aikosh.indiaai.gov.in | Dashboard account only | N/A | Needs download | High |
| Kaggle account | https://kaggle.com | Dashboard account only | N/A | Needs download | High |
| Hugging Face account | https://huggingface.co | Dashboard account only | `HF_TOKEN` | Wired now | High |
| OpenWeather account | https://openweathermap.org | Dashboard account only | `OPENWEATHER_API_KEY` | Wired now | High |
| openrouteservice account | https://openrouteservice.org | Dashboard account only | `OPENROUTESERVICE_API_KEY` | Wired now | Critical |

## 2. Backend env values and config

Target file: [backend/.env.example](C:/Hackathons/IITM/SafeVixAI/backend/.env.example) -> copy to `backend/.env`

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Environment mode | Manual value | `backend/.env` | `ENVIRONMENT` | Needs value | High |
| Allowed frontend origins | Manual value | `backend/.env` | `CORS_ORIGINS` | Wired now | High |
| PostgreSQL connection string | Supabase -> Settings -> Database -> URI | `backend/.env` | `DATABASE_URL` | Needs value | Critical |
| Redis connection string | Upstash -> Connect -> `.env` tab | `backend/.env` | `REDIS_URL` | Needs value | Critical |
| DB pool size | Manual tuning | `backend/.env` | `DB_POOL_SIZE` | Wired now | Medium |
| DB max overflow | Manual tuning | `backend/.env` | `DB_MAX_OVERFLOW` | Wired now | Medium |
| DB pool timeout | Manual tuning | `backend/.env` | `DB_POOL_TIMEOUT_SECONDS` | Wired now | Medium |
| DB recycle time | Manual tuning | `backend/.env` | `DB_POOL_RECYCLE_SECONDS` | Wired now | Medium |
| Supabase URL | Supabase -> Settings -> API | `backend/.env` | `SUPABASE_URL` | Needs value | Critical |
| Supabase anon key | Supabase -> Settings -> API | `backend/.env` | `SUPABASE_ANON_KEY` | Needs value | Critical |
| Supabase service role key | Supabase -> Settings -> API | `backend/.env` | `SUPABASE_SERVICE_ROLE_KEY` | Needs value | Critical |
| Default search radius | Manual value | `backend/.env` | `DEFAULT_RADIUS` | Wired now | Medium |
| Max search radius | Manual value | `backend/.env` | `MAX_RADIUS` | Wired now | Medium |
| Emergency minimum results | Manual value | `backend/.env` | `EMERGENCY_MIN_RESULTS` | Wired now | Medium |
| Emergency radius steps | Manual value | `backend/.env` | `EMERGENCY_RADIUS_STEPS` | Wired now | Medium |
| Cache TTL | Manual value | `backend/.env` | `CACHE_TTL_SECONDS` | Wired now | Medium |
| Geocode cache TTL | Manual value | `backend/.env` | `GEOCODE_CACHE_TTL_SECONDS` | Wired now | Medium |
| Authority cache TTL | Manual value | `backend/.env` | `AUTHORITY_CACHE_TTL_SECONDS` | Wired now | Medium |
| Primary Overpass endpoint | Public OSM | `backend/.env` | `OVERPASS_URL` | Wired now | Critical |
| Overpass mirror list | Public OSM mirrors | `backend/.env` | `OVERPASS_URLS` | Wired now | High |
| Nominatim reverse geocoder | Public OSM | `backend/.env` | `NOMINATIM_URL` | Wired now | Critical |
| Photon search geocoder | Public Photon | `backend/.env` | `PHOTON_URL` | Wired now | Critical |
| openrouteservice base URL | openrouteservice docs | `backend/.env` | `OPENROUTESERVICE_BASE_URL` | Wired now | High |
| openrouteservice API key | openrouteservice dashboard | `backend/.env` | `OPENROUTESERVICE_API_KEY` | Needs value | Critical |
| HTTP user-agent string | Manual value with your email/site | `backend/.env` | `HTTP_USER_AGENT` | Needs value | Critical |
| Request timeout | Manual value | `backend/.env` | `REQUEST_TIMEOUT_SECONDS` | Wired now | Medium |
| Upstream retry attempts | Manual value | `backend/.env` | `UPSTREAM_RETRY_ATTEMPTS` | Wired now | Medium |
| Upstream retry backoff | Manual value | `backend/.env` | `UPSTREAM_RETRY_BACKOFF_SECONDS` | Wired now | Medium |
| data.gov.in API key | data.gov.in account | `backend/.env` | `DATA_GOV_API_KEY` | Needs value | High |
| OpenWeather API key | OpenWeather dashboard | `backend/.env` | `OPENWEATHER_API_KEY` | Needs value | High |
| OpenWeather base URL | OpenWeather docs | `backend/.env` | `OPENWEATHER_BASE_URL` | Wired now | Medium |
| OpenWeather units | Manual value | `backend/.env` | `OPENWEATHER_UNITS` | Wired now | Medium |
| Chatbot mode | Manual value | `backend/.env` | `CHATBOT_MODE` | Wired now | Medium |
| Chatbot ready flag | Manual value | `backend/.env` | `CHATBOT_READY` | Wired now | Medium |
| Local upload base URL | Manual value or storage URL | `backend/.env` | `LOCAL_UPLOAD_BASE_URL` | Needs value | Medium |
| Max upload size | Manual value | `backend/.env` | `MAX_UPLOAD_BYTES` | Wired now | Medium |
| Allowed upload MIME types | Manual value | `backend/.env` | `ALLOWED_UPLOAD_CONTENT_TYPES` | Wired now | Medium |
| Offline bundle directory | Manual path | `backend/.env` | `OFFLINE_BUNDLE_DIR` | Wired now | Medium |
| Route cache TTL | Manual value | `backend/.env` | `ROUTE_CACHE_TTL_SECONDS` | Wired now | Medium |

## 3. Frontend env values and config

Target file: [frontend/.env.example](C:/Hackathons/IITM/SafeVixAI/frontend/.env.example) -> copy to `frontend/.env`

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Backend API URL | Your local backend or deployed backend URL | `frontend/.env` | `NEXT_PUBLIC_API_URL` | Needs value | Critical |
| Supabase project URL | Supabase -> Settings -> API | `frontend/.env` | `NEXT_PUBLIC_SUPABASE_URL` | Needs value | Critical |
| Supabase anon key | Supabase -> Settings -> API | `frontend/.env` | `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Needs value | Critical |
| Live map default zoom | Manual value | `frontend/.env` | `NEXT_PUBLIC_MAP_DEFAULT_ZOOM` | Wired now | Medium |
| Fallback map latitude | Manual value | `frontend/.env` | `NEXT_PUBLIC_MAP_FALLBACK_LAT` | Wired now | Medium |
| Fallback map longitude | Manual value | `frontend/.env` | `NEXT_PUBLIC_MAP_FALLBACK_LON` | Wired now | Medium |
| Fallback map zoom | Manual value | `frontend/.env` | `NEXT_PUBLIC_MAP_FALLBACK_ZOOM` | Wired now | Medium |
| Primary map style URL | OpenFreeMap Liberty | `frontend/.env` | `NEXT_PUBLIC_MAP_STYLE_URL` | Wired now | Critical |
| MapTiler key | MapTiler dashboard | `frontend/.env` | `NEXT_PUBLIC_MAPTILER_KEY` | Skip | Low |
| MapTiler style id | Manual value | `frontend/.env` | `NEXT_PUBLIC_MAPTILER_STYLE_ID` | Skip | Low |

## 4. Chatbot env values and config

Target file: `chatbot_service/.env`

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Environment mode | Manual value | `chatbot_service/.env` | `ENVIRONMENT` | Complete | Medium |
| Chatbot service name | Manual value | `chatbot_service/.env` | `CHATBOT_SERVICE_NAME` | Complete | Medium |
| Chatbot service port | Manual value | `chatbot_service/.env` | `CHATBOT_SERVICE_PORT` | Complete | Medium |
| Allowed origins | Manual value | `chatbot_service/.env` | `CORS_ORIGINS` | Complete | Medium |
| Main backend base URL | Local or deployed backend | `chatbot_service/.env` | `MAIN_BACKEND_BASE_URL` | Complete | Critical |
| Main backend timeout | Manual value | `chatbot_service/.env` | `MAIN_BACKEND_TIMEOUT_SECONDS` | Complete | Medium |
| Redis URL | Upstash -> Connect | `chatbot_service/.env` | `REDIS_URL` | Complete | High |
| Chroma persist directory | Manual path | `chatbot_service/.env` | `CHROMA_PERSIST_DIR` | Complete | High |
| RAG data directory | Manual path | `chatbot_service/.env` | `RAG_DATA_DIR` | Complete | High |
| Embedding model | LocalHashEmbeddingFunction | `chatbot_service/.env` | `EMBEDDING_MODEL` | Complete | Critical |
| Retrieval top-k | Manual value | `chatbot_service/.env` | `TOP_K_RETRIEVAL` | Complete | Medium |
| Default provider | Manual value | `chatbot_service/.env` | `DEFAULT_LLM_PROVIDER` | Complete | High |
| Default model | Manual value | `chatbot_service/.env` | `DEFAULT_LLM_MODEL` | Complete | High |
| Groq API key | https://console.groq.com | `chatbot_service/.env` | `GROQ_API_KEY` | Complete | Critical |
| Gemini model name | Manual value | `chatbot_service/.env` | `GEMINI_MODEL` | Complete | High |
| Google API key | https://aistudio.google.com | `chatbot_service/.env` | `GOOGLE_API_KEY` | Complete | Critical |
| GitHub token | https://github.com/marketplace/models | `chatbot_service/.env` | `GITHUB_TOKEN` | Complete | High |
| Mistral API key | https://console.mistral.ai | `chatbot_service/.env` | `MISTRAL_API_KEY` | Complete | Medium |
| Together AI key | https://api.together.xyz | `chatbot_service/.env` | `TOGETHER_API_KEY` | Complete | Medium |
| NVIDIA NIM key | https://build.nvidia.com | `chatbot_service/.env` | `NVIDIA_NIM_API_KEY` | Complete | Medium |
| NVIDIA NIM base URL | Hosted NVIDIA endpoint or self-hosted URL | `chatbot_service/.env` | `NVIDIA_NIM_BASE_URL` | Complete | Low |
| OpenAI API key | https://platform.openai.com | `chatbot_service/.env` | `OPENAI_API_KEY` | Skip | Low |
| OpenWeather API key | OpenWeather dashboard | `chatbot_service/.env` | `OPENWEATHER_API_KEY` | Complete | Medium |
| OpenWeather base URL | OpenWeather docs | `chatbot_service/.env` | `OPENWEATHER_BASE_URL` | Complete | Medium |
| OpenWeather units | Manual value | `chatbot_service/.env` | `OPENWEATHER_UNITS` | Complete | Low |
| HTTP timeout | Manual value | `chatbot_service/.env` | `HTTP_TIMEOUT_SECONDS` | Complete | Medium |
| Chatbot user-agent | Manual value | `chatbot_service/.env` | `HTTP_USER_AGENT` | Complete | Medium |
| Hugging Face token | https://huggingface.co/settings/tokens | `chatbot_service/.env` | `HF_TOKEN` | Complete | High |
| Cerebras API key | https://cloud.cerebras.ai | `chatbot_service/.env` | `CEREBRAS_API_KEY` | Complete | High |
| OpenRouter API key | https://openrouter.ai | `chatbot_service/.env` | `OPENROUTER_API_KEY` | Complete | Medium |

## 5. Map and geospatial runtime stack

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| MapLibre GL JS | https://maplibre.org and npm | [frontend/package.json](C:/Hackathons/IITM/SafeVixAI/frontend/package.json) | N/A | Wired now | Critical |
| OpenFreeMap Liberty style | https://tiles.openfreemap.org/styles/liberty | [frontend/components/maps/MapLibreCanvas.tsx](C:/Hackathons/IITM/SafeVixAI/frontend/components/maps/MapLibreCanvas.tsx) and `frontend/.env` | `NEXT_PUBLIC_MAP_STYLE_URL` | Wired now | Critical |
| OpenFreeMap Positron style | https://tiles.openfreemap.org/styles/positron | Future style toggle or theme config | N/A | Future phase | Low |
| Carto Voyager backup style | https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json | Future fallback in `frontend/components/maps/MapLibreCanvas.tsx` | N/A | Future phase | High |
| Carto Dark Matter style | Carto CDN | Future dark-mode style toggle | N/A | Future phase | Medium |
| Photon search geocoder | https://photon.komoot.io/api | [backend/core/config.py](C:/Hackathons/IITM/SafeVixAI/backend/core/config.py), `backend/.env` | `PHOTON_URL` | Wired now | Critical |
| Nominatim reverse geocoder | https://nominatim.openstreetmap.org | [backend/core/config.py](C:/Hackathons/IITM/SafeVixAI/backend/core/config.py), `backend/.env` | `NOMINATIM_URL` | Wired now | Critical |
| Overpass API | https://overpass-api.de/api/interpreter | [backend/core/config.py](C:/Hackathons/IITM/SafeVixAI/backend/core/config.py), `backend/.env` | `OVERPASS_URL` | Wired now | Critical |
| Overpass mirror list | `overpass.kumi.systems`, `overpass.private.coffee` | `backend/.env` | `OVERPASS_URLS` | Wired now | High |
| openrouteservice routing | https://api.openrouteservice.org | [backend/services/routing_service.py](C:/Hackathons/IITM/SafeVixAI/backend/services/routing_service.py), `backend/.env` | `OPENROUTESERVICE_BASE_URL`, `OPENROUTESERVICE_API_KEY` | Wired now | Critical |
| PMTiles runtime | https://github.com/protomaps/PMTiles | `frontend/public/maps/india.pmtiles` and future PMTiles loader | N/A | Future phase | Medium |

## 6. Government and public datasets for maps and reporting

Suggested local dataset root: `SafeVixAI/backend/datasets/`

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| National Hospital Directory CSV | https://data.gov.in/catalog/hospital-directory-national-health-portal | `backend/datasets/hospital_directory_nhp.csv` | `DATA_GOV_API_KEY` if API-based | Needs download | Critical |
| Police Station Directory | data.gov.in search `police stations` | `backend/datasets/police_stations.csv` | `DATA_GOV_API_KEY` if API-based | Needs download | High |
| PMGSY Rural Roads export | data.gov.in search `PMGSY` or PMGSY/OMMAS export | `backend/datasets/pmgsy/pmgsy_<state>.csv` or `.zip` | `DATA_GOV_API_KEY` if API-based | Needs download | High |
| District Boundaries GeoJSON | data.gov.in | `backend/datasets/district_boundaries.geojson` | `DATA_GOV_API_KEY` if API-based | Needs download | Medium |
| NHM Health Facilities | https://nhm.gov.in | `backend/datasets/nhm_health_facilities.csv` | N/A | Future phase | Medium |
| TN road GeoJSON | Your downloaded state road dataset | `backend/datasets/tamil_nadu_roads.geojson` | N/A | Partially wired via importer | Medium |
| KA road GeoJSON | Your downloaded state road dataset | `backend/datasets/karnataka_roads.geojson` | N/A | Partially wired via importer | Medium |
| Maharashtra highways GeoJSON | State portal export | `backend/datasets/maharashtra_highways.geojson` | N/A | Partially wired via importer | Medium |
| City corporation streets CSV | Local body portal export | `backend/datasets/city_corporation_streets.csv` | N/A | Partially wired via importer | Low |

## 7. Accident, risk, and road safety datasets

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| MAARG ONNX model | AI Kosh Project MAARG | `frontend/public/models/maarg-risk.onnx` | N/A | Future phase | High |
| MoRTH accidents by vehicle type 2012-2016 | AI Kosh / MoRTH | `backend/datasets/accidents/morth_vehicle_type_2012_2016.csv` | N/A | Needs download | Critical |
| MoRTH accidents by road features 2014-2016 | AI Kosh / MoRTH | `backend/datasets/accidents/morth_road_features_2014_2016.csv` | N/A | Needs download | Critical |
| Persons injured 2011-2014 | AI Kosh / MoRTH | `backend/datasets/accidents/morth_persons_injured_2011_2014.csv` | N/A | Needs download | Medium |
| India Road Accident with lat/lon | Kaggle `data125661` | `backend/datasets/accidents/india_road_accident_coords.csv` | N/A | Needs download | Medium |
| Road Accident Severity dataset | Kaggle `khushi` | `backend/datasets/accidents/road_accident_severity.csv` | N/A | Future phase | Low |
| Road Accidents India (Manu Gupta) | Kaggle | `backend/datasets/accidents/road_accidents_india_manu_gupta.csv` | N/A | Needs download | Low |
| Crime Review India 2025 | AI Kosh / IndiaAI | `backend/datasets/crime_review_india_2025.csv` | N/A | Future phase | Low |

## 8. Pothole and road damage vision datasets

Keep raw training datasets outside git if possible.

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Potholes YOLOv8 (Anggadwi) | https://kaggle.com/anggadwisunarto/potholes-detection-yolov8 | `C:/datasets/potholes/anggadwi_yolov8/` | N/A | Needs download | High |
| Pothole dataset (Sachin Patel) | https://kaggle.com/sachinpatel21/pothole-image-dataset | `C:/datasets/potholes/sachin_patel/` | N/A | Needs download | Medium |
| Pothole dataset (Andrew) | https://kaggle.com/andrewmvd/pothole-detection | `C:/datasets/potholes/andrew_pascal_voc/` | N/A | Needs download | Low |
| Road Damage Dataset 2025 | https://zenodo.org/records/17834373 | `C:/datasets/road_damage_2025/` | N/A | Needs download | High |
| Potholes + Cracks + Manholes | Kaggle `sabidrahman` | `C:/datasets/potholes_cracks_manholes/` | N/A | Needs download | Low |

## 9. Legal, first-aid, and RAG document corpus

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Motor Vehicles Act 1988 PDF | https://www.indiacode.nic.in | `backend/data/motor_vehicles_act_1988.pdf` | N/A | Complete | Critical |
| MV Amendment Act 2019 PDF | https://morth.nic.in | `backend/data/mv_amendment_act_2019.pdf` | N/A | Complete | Critical |
| WHO Trauma Care Guidelines PDF | https://www.who.int | `backend/data/who_trauma_care_guidelines.pdf` | N/A | Complete | Critical |
| WHO Global Road Safety Report 2023 PDF | https://www.who.int/publications/i/item/9789240086517 | `backend/data/who_road_safety_2023.pdf` | N/A | Needs download | High |
| State amendment PDFs | State transport department websites | `backend/data/state_amendments/<state>.pdf` | N/A | Needs download | High |
| Indian Kanoon MV Act judgments | https://indiankanoon.org | `backend/data/legal_cases/*.pdf` | N/A | Needs download | High |
| BhasaAnuvaad speech corpus | AI Kosh / AI4Bharat | `C:/datasets/bhasaanuvaad/` | N/A | Future phase | Low |
| BharatGen MHQA multilingual QA | AI Kosh / IIT Bombay | `backend/data/bharatgen_mhqa/` | N/A | Future phase | Low |

## 10. Embedding, offline AI, and hosted LLM models

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| LocalHashEmbeddingFunction embeddings | `LocalHashEmbeddingFunction (zero-dependency)` on Hugging Face | `chatbot_service/.env` plus `chatbot_service/rag/embeddings.py` | `EMBEDDING_MODEL` | Complete | Critical |
| multilingual MiniLM embeddings | `hash-based embeddings/paraphrase-multilingual-MiniLM-L12-v2` | Future `chatbot_service/rag/embeddings.py` | `EMBEDDING_MODEL` or upgrade path | Future phase | High |
| Gemma 4 E2B | `google/gemma-4-E2B-it` | [frontend/lib/edge-ai.ts](C:/Hackathons/IITM/SafeVixAI/frontend/lib/edge-ai.ts) | N/A | Future phase | Critical |
| Gemma 4 E4B | `google/gemma-4-E4B-it` | [frontend/lib/edge-ai.ts](C:/Hackathons/IITM/SafeVixAI/frontend/lib/edge-ai.ts) or future offline vision module | N/A | Future phase | High |
| Gemma 4 26B A4B | `google/gemma-4-26B-A4B-it` | Future server-side inference path only | N/A | Future phase | Low |
| Gemma 4 31B Dense | `google/gemma-4-31B-it` | Future server-side inference path only | N/A | Future phase | Low |
| Sarvam-30B | AI Kosh / Hugging Face inference | `chatbot_service/providers/sarvam_provider.py` | `HF_TOKEN` | Complete | Critical |
| Sarvam-105B | AI Kosh / Hugging Face inference | `chatbot_service/providers/sarvam_provider.py` | `HF_TOKEN` | Complete | High |
| SarvamM | AI Kosh / Hugging Face inference | `chatbot_service/providers/sarvam_provider.py` | `HF_TOKEN` | Complete | High |
| SarvamTranslate | AI Kosh / Hugging Face inference | Future translation provider | `HF_TOKEN` | Complete | Medium |
| Shuka-v1 | AI Kosh / Hugging Face inference | Future voice report service | `HF_TOKEN` | Future phase | Medium |
| BharatGen Param-2 17B | `bharatgenai/param2-17b-moe-a2.4b` | Future `chatbot_service/providers/bharatgen_provider.py` | `HF_TOKEN` | Future phase | High |
| BharatGen Sooktam-2 | `bharatgenai/sooktam2` | Future `chatbot_service/voice/speak.py` or `voice/providers/` | `HF_TOKEN` or provider key if using hosted API | Future phase | High |
| BharatGen A2TTS | BharatGen / AI Kosh | Future `chatbot_service/voice/tts/` | N/A | Future phase | Low |
| Whisper large-v3 | Hugging Face | Future ASR fallback in chatbot service | `HF_TOKEN` | Future phase | Medium |

## 11. Voice and ASR models

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| IndicSeamless ASR/TTS (14 languages) | AI Kosh / AI4Bharat | `chatbot_service/services/speech_translation.py` | `HF_TOKEN` if hosted | Complete | Critical |
| IndicWav2Vec Hindi | AI Kosh / AI4Bharat | Future `chatbot_service/voice/indic_asr.py` | `HF_TOKEN` if hosted | Future phase | Critical |
| IndicWav2Vec Tamil | AI Kosh / AI4Bharat | Same as above | `HF_TOKEN` if hosted | Future phase | Critical |
| IndicWav2Vec Telugu | AI Kosh | Same as above | `HF_TOKEN` if hosted | Future phase | High |
| IndicWav2Vec Gujarati | AI Kosh | Same as above | `HF_TOKEN` if hosted | Future phase | High |
| IndicWav2Vec Marathi | AI Kosh | Same as above | `HF_TOKEN` if hosted | Future phase | High |
| IndicWav2Vec Odia | AI Kosh | Same as above | `HF_TOKEN` if hosted | Future phase | Medium |
| IndicWav2Vec Bengali | AI Kosh | Same as above | `HF_TOKEN` if hosted | Future phase | High |
| IndicConformer Kannada | AI Kosh | Same as above | `HF_TOKEN` if hosted | Future phase | High |
| IndicConformer Maithili | AI Kosh | Same as above | `HF_TOKEN` if hosted | Future phase | Medium |

## 12. LLM provider chain from the document

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Groq provider | https://console.groq.com | `chatbot_service/providers/groq_provider.py` | `GROQ_API_KEY` | Complete | Critical |
| Cerebras provider | https://cloud.cerebras.ai | `chatbot_service/providers/cerebras_provider.py` | `CEREBRAS_API_KEY` | Complete | High |
| Sarvam via HF Inference | Hugging Face | `chatbot_service/providers/sarvam_provider.py` | `HF_TOKEN` | Complete | High |
| BharatGen via HF Inference | Hugging Face | Future `chatbot_service/providers/bharatgen_provider.py` | `HF_TOKEN` | Future phase | Medium |
| Gemini 1.5 Flash | https://aistudio.google.com | `chatbot_service/providers/gemini_provider.py` | `GOOGLE_API_KEY`, `GEMINI_MODEL` | Complete | High |
| GitHub Models | https://github.com/marketplace/models | `chatbot_service/providers/github_models_provider.py` | `GITHUB_TOKEN` | Complete | Medium |
| NVIDIA NIM hosted models | https://build.nvidia.com | `chatbot_service/providers/nvidia_nim_provider.py` | `NVIDIA_NIM_API_KEY`, `NVIDIA_NIM_BASE_URL` | Complete | Medium |
| OpenRouter | https://openrouter.ai | `chatbot_service/providers/openrouter_provider.py` | `OPENROUTER_API_KEY` | Complete | Medium |
| Mistral | https://console.mistral.ai | `chatbot_service/providers/mistral_provider.py` | `MISTRAL_API_KEY` | Complete | Low |
| Together AI | https://api.together.xyz | `chatbot_service/providers/together_provider.py` | `TOGETHER_API_KEY` | Complete | Low |
| Provider Router with circuit breaker | — | `chatbot_service/providers/router.py`, `chatbot_service/providers/provider_router.py` | `DEFAULT_LLM_PROVIDER`, `DEFAULT_LLM_MODEL` | Complete | Critical |

## 13. Offline map and browser-side model artifacts

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| India PMTiles extract | Protomaps / PMTiles downloads | `frontend/public/maps/india.pmtiles` | N/A | Future phase | Medium |
| WebLLM Phi-3 Mini (2.2GB) | Microsoft / Hugging Face | Runtime browser cache (on-demand download) | N/A | Complete | High |
| LocalHashEmbeddingFunction (zero-dependency) | ChromaDB bundled | Runtime browser cache | N/A | Complete | Medium |
| YOLOv8n browser ONNX | Xenova/yolov8n or fine-tuned ONNX export | `frontend/public/models/` — loaded via @huggingface/transformers | N/A | Complete | High |
| GeoJSON offline data bundles | Generated by backend | `frontend/public/offline-data/` — `india-emergency.geojson`, city bundles | N/A | Complete | High |

## 14. Mobile-only future references from the document

These are not for the current web repo, but they are mentioned in the source document and are included here so nothing is lost.

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Android AICore path for Gemma 4 | Android AICore / Google | N/A (future Android app only) | N/A | Future phase | Low |
| ML Kit GenAI Prompt API | Google ML Kit / Android | N/A (future Android app only) | N/A | Future phase | Low |

## 15. Manual directories you should create locally

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Backend dataset root | Manual local folder | `backend/datasets/` | N/A | Needs download | High |
| Backend accident datasets folder | Manual local folder | `backend/datasets/accidents/` | N/A | Needs download | High |
| Backend legal cases folder | Manual local folder | `backend/data/legal_cases/` | N/A | Needs download | High |
| Backend Chroma vector store | Built by vectorstore job | `backend/data/chroma_db/` | `CHROMA_PERSIST_DIR` or project default path | Complete | High |
| Frontend model assets folder | Manual local folder | `frontend/public/models/` | N/A | Complete | High |
| Frontend offline map assets folder | Manual local folder | `frontend/public/offline-data/` | N/A | Complete | High |
| Chatbot service Chroma vector store | Built by vectorstore job | `chatbot_service/data/chroma_db/` | N/A | Complete | Critical |
| Chatbot service first-aid JSON corpus | Manual or sourced | `chatbot_service/data/first_aid.json` | N/A | Complete | High |

## 16. Resources the document explicitly says to skip or avoid as the main path

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| MapTiler as primary production map | https://www.maptiler.com | N/A | `NEXT_PUBLIC_MAPTILER_KEY` | Skip | Low |
| Google Maps API as primary map stack | https://mapsplatform.google.com | N/A | N/A | Skip | Low |
| Mapbox as primary map stack | https://www.mapbox.com | N/A | N/A | Skip | Low |
| Firebase Realtime Database | https://firebase.google.com | N/A | N/A | Skip | Low |
| OpenAI GPT-4 as default paid path | https://platform.openai.com | N/A | `OPENAI_API_KEY` | Skip | Low |
| Gnani Vachana TTS | AI Kosh | N/A | N/A | Skip | Low |
| DeepSeek direct API | DeepSeek | N/A | N/A | Skip | Low |
| Phi-3 Mini offline model | Microsoft / Hugging Face | Old offline path in `frontend/lib/edge-ai.ts` | N/A | Skip | Low |
| Sarvam-1 2B original | AI Kosh | N/A | N/A | Skip | Low |
| RomanSetu transliteration | AI Kosh | N/A | N/A | Skip | Low |
| GenLoop 2B small models | AI Kosh | N/A | N/A | Skip | Low |
| Meteorological raw datasets | AI Kosh | N/A | N/A | Skip | Low |

## 17. Recommended collection order

1. Supabase values:
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
2. `REDIS_URL`
3. `OPENROUTESERVICE_API_KEY`
4. `OPENWEATHER_API_KEY`
5. `DATA_GOV_API_KEY`
6. National Hospital Directory CSV
7. 3 MoRTH accident CSVs
8. Police Station Directory
9. PMGSY roads export
10. District Boundaries GeoJSON
11. MAARG ONNX
12. Legal PDFs:
    - MV Act 1988
    - MV Amendment 2019
    - WHO Trauma
    - WHO Road Safety
    - state amendment PDFs
    - Indian Kanoon judgments
13. Chatbot provider keys:
    - Groq
    - Google
    - GitHub Models
    - NVIDIA NIM
    - Mistral
    - Together AI
    - HF token
    - Cerebras
    - OpenRouter
14. Optional later-phase assets:
    - PMTiles India extract
    - pothole training datasets
    - BhasaAnuvaad
    - BharatGen/Sarvam voice and multilingual QA add-ons

## 18. Current repo reality check

This checklist intentionally includes more than the current repo already supports.

Already wired in current code:
- MapLibre renderer
- OpenFreeMap default map style
- Photon + Nominatim pattern
- Overpass emergency POIs
- openrouteservice route plumbing
- emergency seeding scaffold
- road infrastructure import scaffold
- **Chatbot provider chain** (10 providers: Groq→Cerebras→Gemini→GitHub→NVIDIA→OpenRouter→Mistral→Together→Template)
- **Intent detector** (9 intent classes)
- **All 13 agent tools** (SOS, Challan, LegalSearch, FirstAid, Weather, OpenMeteo, RoadInfra, RoadIssues, SubmitReport, Geocoding, DrugInfo, What3Words, Emergency)
- **Conversation memory** (Redis, 24-hour TTL)
- **Safety checker** (7-layer defense)
- **Speech/ASR** (IndicSeamless, 14 languages)
- **Offline AI** (WebLLM Phi-3 Mini, 2.2GB on-demand download)
- **Crash detection** (DeviceMotion API, 2.5G threshold, CrashCountdown UI)
- **All 25 features** fully implemented

Still only partially wired or not wired yet:
- NHP hospital importer
- MoRTH accident ingestion and blackspot tables
- MAARG ONNX heatmap
- PMTiles offline maps
- Gemma 4 offline edge AI replacement
- BharatGen provider
- IndicWav2Vec / IndicConformer / Sooktam-2 voice stack (IndicSeamless is used instead)

## 19. Developer tooling, team workflow, and project setup assets

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Shared password manager for keys | Bitwarden or equivalent | Team vault only | N/A | Reference only | Critical |
| Cursor AI IDE | https://cursor.sh | Developer machine only | N/A | Reference only | Medium |
| Windsurf IDE / extension | https://windsurf.ai | Developer machine only | N/A | Reference only | Medium |
| 21st.dev chat UI reference | https://21st.dev | No repo save path required unless you export components | N/A | Reference only | Low |
| Python 3.11 virtualenv for chatbot service | Python.org / local environment | `chatbot_service/.venv/` | N/A | Complete | High |
| VS Code Python extension | VS Code Marketplace | Developer machine only | N/A | Reference only | Low |
| VS Code Pylance extension | VS Code Marketplace | Developer machine only | N/A | Reference only | Low |
| Ruff extension / linter support | VS Code Marketplace / Python package | Developer machine only and `chatbot_service/requirements.txt` | N/A | Complete | Low |
| Black formatter support | VS Code Marketplace / Python package | Developer machine only and `chatbot_service/requirements.txt` | N/A | Complete | Low |
| REST Client extension | VS Code Marketplace | Developer machine only | N/A | Reference only | Low |
| GitHub `main` integration branch | GitHub repo branch strategy | Remote branch only | N/A | Reference only | High |
| Render staging chatbot instance | https://render.com | Render dashboard only | N/A | Complete | High |
| Render production chatbot instance | https://render.com | Render dashboard only | N/A | Complete | High |

## 20. Chatbot service root files and deployment artifacts

Target root: `chatbot_service/`

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Chatbot FastAPI entrypoint | — | `chatbot_service/main.py` | N/A | Complete | Critical |
| Chatbot Python dependencies | — | `chatbot_service/requirements.txt` | N/A | Complete | Critical |
| Chatbot Dockerfile | — | `chatbot_service/Dockerfile` | N/A | Complete | Critical |
| Chatbot env template | — | `chatbot_service/.env.example` | N/A | Complete | Critical |
| Chatbot gitignore | — | `chatbot_service/.gitignore` | N/A | Complete | High |
| Chatbot Render blueprint | — | `chatbot_service/render.yaml` | N/A | Complete | High |
| Chatbot config module | — | `chatbot_service/config.py` | N/A | Complete | Critical |
| Chatbot service health endpoint | — | `chatbot_service/main.py` | N/A | Complete | High |
| Chatbot service port 8010 binding | — | `chatbot_service/main.py` and `chatbot_service/.env` | `CHATBOT_SERVICE_PORT` | Complete | High |
| Chroma build baked into Docker image | — | `chatbot_service/Dockerfile` and `chatbot_service/data/build_vectorstore.py` | N/A | Complete | Medium |

## 21. Chatbot service code artifacts by subsystem

### 21.1 Providers

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Provider base class | — | `chatbot_service/providers/base.py` | N/A | Complete | Critical |
| Groq provider wrapper | — | `chatbot_service/providers/groq_provider.py` | `GROQ_API_KEY` | Complete | Critical |
| Gemini provider wrapper | — | `chatbot_service/providers/gemini_provider.py` | `GOOGLE_API_KEY`, `GEMINI_MODEL` | Complete | High |
| GitHub Models provider wrapper | — | `chatbot_service/providers/github_models_provider.py` | `GITHUB_TOKEN` | Complete | High |
| NVIDIA NIM provider wrapper | — | `chatbot_service/providers/nvidia_nim_provider.py` | `NVIDIA_NIM_API_KEY`, `NVIDIA_NIM_BASE_URL` | Complete | Medium |
| Mistral provider wrapper | — | `chatbot_service/providers/mistral_provider.py` | `MISTRAL_API_KEY` | Complete | Medium |
| Together AI provider wrapper | — | `chatbot_service/providers/together_provider.py` | `TOGETHER_API_KEY` | Complete | Medium |
| Cerebras provider wrapper | — | `chatbot_service/providers/cerebras_provider.py` | `CEREBRAS_API_KEY` | Complete | High |
| OpenRouter provider wrapper | — | `chatbot_service/providers/openrouter_provider.py` | `OPENROUTER_API_KEY` | Complete | Medium |
| Template provider (deterministic fallback) | — | `chatbot_service/providers/template_provider.py` | N/A | Complete | Critical |
| Provider router with circuit breaker | — | `chatbot_service/providers/router.py`, `chatbot_service/providers/provider_router.py` | `DEFAULT_LLM_PROVIDER`, `DEFAULT_LLM_MODEL` | Complete | Critical |

### 21.2 RAG, agent, and orchestration

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Chroma vectorstore manager | — | `chatbot_service/rag/vectorstore.py` | `CHROMA_PERSIST_DIR` | Complete | Critical |
| Embeddings wrapper | — | `chatbot_service/rag/embeddings.py` | `EMBEDDING_MODEL` | Complete | Critical |
| Retriever module | — | `chatbot_service/rag/retriever.py` | `TOP_K_RETRIEVAL` | Complete | High |
| PDF/document loader | — | `chatbot_service/rag/document_loader.py` | `RAG_DATA_DIR` | Complete | High |
| ChatEngine definition | — | `chatbot_service/agent/graph.py` | N/A | Complete | Critical |
| Agent state schema | — | `chatbot_service/agent/state.py` | N/A | Complete | High |
| Intent detector | — | `chatbot_service/agent/intent_detector.py` (9 intent classes) | N/A | Complete | Critical |
| Context assembler | — | `chatbot_service/agent/context_assembler.py` | N/A | Complete | Critical |
| Safety checker | — | `chatbot_service/agent/safety_checker.py` (7-layer defense) | N/A | Complete | High |

### 21.3 Tools, memory, API, and tests

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| SOS API tool | — | `chatbot_service/tools/sos_tool.py` | `MAIN_BACKEND_BASE_URL` | Complete | Critical |
| Emergency tool | — | `chatbot_service/tools/emergency_tool.py` | `MAIN_BACKEND_BASE_URL` | Complete | Critical |
| Challan tool | — | `chatbot_service/tools/challan_tool.py` | `MAIN_BACKEND_BASE_URL` | Complete | Critical |
| Legal search tool | — | `chatbot_service/tools/legal_search_tool.py` | N/A | Complete | High |
| Road infrastructure tool | — | `chatbot_service/tools/road_infra_tool.py` | `MAIN_BACKEND_BASE_URL` | Complete | High |
| Road issues tool | — | `chatbot_service/tools/road_issues_tool.py` | `MAIN_BACKEND_BASE_URL` | Complete | High |
| First-aid tool | — | `chatbot_service/tools/first_aid_tool.py` | N/A | Complete | High |
| Weather tool | — | `chatbot_service/tools/weather_tool.py` | `OPENWEATHER_API_KEY` | Complete | Medium |
| Open-Meteo tool | — | `chatbot_service/tools/open_meteo.py` | N/A | Complete | Medium |
| Submit-report tool | — | `chatbot_service/tools/submit_report_tool.py` | `MAIN_BACKEND_BASE_URL` | Complete | High |
| Geocoding tool | — | `chatbot_service/tools/geocoding.py` | N/A | Complete | High |
| Drug Info tool | — | `chatbot_service/tools/drug_info.py` | N/A | Complete | Medium |
| What3Words tool | — | `chatbot_service/tools/what3words.py` | N/A | Complete | Medium |
| Redis conversation memory | — | `chatbot_service/memory/redis_memory.py` | `REDIS_URL` | Complete | High |
| Chat REST and SSE API | — | `chatbot_service/api/chat.py` | N/A | Complete | Critical |
| Chat message endpoint | — | `chatbot_service/api/chat.py` -> `POST /api/v1/chat/` | N/A | Complete | Critical |
| Chat stream endpoint | — | `chatbot_service/api/chat.py` -> `POST /api/v1/chat/stream` | N/A | Complete | Critical |
| Chat history endpoint | — | `chatbot_service/api/chat.py` -> `GET /api/v1/chat/history/{session_id}` | N/A | Complete | Medium |
| Admin endpoints API | — | `chatbot_service/api/admin.py` | N/A | Complete | Medium |
| Provider health admin endpoint | — | `chatbot_service/api/admin.py` -> `GET /admin/provider-health` | N/A | Complete | Medium |
| Vectorstore rebuild admin endpoint | — | `chatbot_service/api/admin.py` -> `POST /admin/rebuild-vectorstore` | N/A | Complete | Medium |
| Chatbot stats admin endpoint | — | `chatbot_service/api/admin.py` -> `GET /admin/stats` | N/A | Complete | Medium |
| Provider integration tests | — | `chatbot_service/tests/test_providers.py` | N/A | Complete | High |
| Intent tests | — | `chatbot_service/tests/test_intent.py` | N/A | Complete | High |
| Tool contract tests | — | `chatbot_service/tests/test_tools.py` | N/A | Complete | High |
| RAG retrieval tests | — | `chatbot_service/tests/test_rag.py` | N/A | Complete | High |
| Voice tests | — | `chatbot_service/tests/test_voice.py` | N/A | Complete | Medium |
| End-to-end chatbot tests | — | `chatbot_service/tests/test_e2e.py` | N/A | Complete | Critical |

## 22. Database tables, runtime channels, offline data files, and helper scripts

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Violations seed CSV | — | `backend/data/violations_seed.csv` | N/A | Complete | Critical |
| State overrides CSV | — | `backend/data/state_overrides.csv` | N/A | Complete | Critical |
| Violations reseed script | — | `backend/data/seed_violations.py` | N/A | Complete | High |
| Offline violations CSV for browser challan | — | `frontend/public/offline-data/violations.csv` | N/A | Complete | High |
| Offline emergency GeoJSON | — | `frontend/public/offline-data/india-emergency.geojson` | N/A | Complete | High |
| Downloadable city/state emergency bundles | — | `frontend/public/offline-data/city-bundles/` or `frontend/public/offline-data/state-packs/` | N/A | Complete | Medium |
| Vectorstore build script | — | `chatbot_service/data/build_vectorstore.py` | N/A | Complete | High |
| Offline first-aid JSON corpus | — | `chatbot_service/data/first_aid.json` | N/A | Complete | High |
| Authority matrix | — | `backend/services/authority_router.py` | N/A | Complete | Critical |
| Road safety score / segment risk dataset | — | Future `backend/data/road_safety_score/` or DB table | N/A | Future phase | Medium |
| Passive road-quality heatmap storage | — | Future DB table / analytics dataset | N/A | Future phase | Low |
| Chatbot service Chroma vectorstore | Built by vectorstore job | `chatbot_service/data/chroma_db/` | N/A | Complete | Critical |

## 23. Browser APIs, client-side runtime assets, and offline storage

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Geolocation one-shot API | — | `frontend/lib/geolocation.ts` | N/A | Wired now | Critical |
| Geolocation continuous watch | — | `frontend/lib/geolocation.ts` | N/A | Wired now | Critical |
| DeviceMotion crash detection | — | `frontend/lib/crash-detection.ts` | N/A | Complete | High |
| Service Worker | — | `frontend/public/sw.js` or Next.js PWA layer | N/A | Complete | High |
| IndexedDB cache | — | `frontend/lib/offline-sos-queue.ts` and browser storage | N/A | Complete | High |
| DuckDB-Wasm | — | `frontend/lib/duckdb-challan.ts` and browser bundle | N/A | Complete | High |
| WebLLM Phi-3 Mini | — | `frontend/lib/offline-ai.ts` and @mlc-ai/web-llm | N/A | Complete | High |
| @huggingface/transformers (YOLO) | — | `frontend/lib/offline-ai.ts` and @huggingface/transformers | N/A | Complete | High |
| Browser Cache Storage for offline models | — | Browser cache only | N/A | Complete | Medium |
| WebSocket stream endpoint | — | `chatbot_service/api/chat.py` and frontend chat client | N/A | Complete | Critical |
| SSE streaming fallback | — | Frontend chat client / API adapter | N/A | Complete | Low |
| Chat session ID stored client-side | — | `frontend/lib/store.ts` or browser storage | N/A | Complete | Medium |
| Web Speech API | — | `frontend/components/chat/VoiceInput.tsx` | N/A | Complete | High |
| Web Speech Synthesis API | — | `frontend/components/chat/VoiceOutput.tsx` | N/A | Complete | High |
| Browser Notification API | — | `frontend/lib/notifications.ts` or alert module | N/A | Future phase | Medium |
| Hands-free mode toggle | — | `frontend/app/settings/page.tsx` and `frontend/components/chat/VoiceOutput.tsx` | N/A | Complete | Medium |
| Trip history in IndexedDB | — | Future `frontend/lib/trip-history.ts` or IndexedDB store | N/A | Future phase | Medium |
| Feedback thumbs up/down UI | — | Future `frontend/components/chat/FeedbackButtons.tsx` | N/A | Future phase | Medium |
| Voice transcript UI | — | `frontend/components/chat/VoiceInput.tsx` | N/A | Complete | Medium |
| Route-to-hospital external deep link | — | `frontend/components/EmergencyMapInner.tsx` or service popup UI | N/A | Future phase | Medium |

## 24. User profile fields, portals, helplines, and authority-routing integrations

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| User blood group field | — | `frontend/app/profile/page.tsx` and IndexedDB persistence (never leaves device) | N/A | Complete | High |
| User vehicle number field | — | `frontend/app/profile/page.tsx` and profile persistence layer | N/A | Complete | High |
| User emergency contacts | — | `frontend/app/profile/page.tsx` and profile persistence layer | N/A | Complete | High |
| Optional disability / medical info | — | `frontend/app/profile/page.tsx` and profile persistence layer | N/A | Future phase | Medium |
| NHAI emergency helpline | Official NHAI / Sukhad Yatra references | UI constants and authority matrix | N/A | Complete | Critical |
| NHAI complaint portal | https://nhai.gov.in/complaint | External link and authority matrix | N/A | Future phase | High |
| PG Portal grievance fallback | https://pgportal.gov.in | External link and authority matrix | N/A | Future phase | High |
| OMMAS / PMGSY complaint routing | https://ommas.nic.in | External link and authority matrix | N/A | Future phase | High |
| Universal authority-routing matrix | — | `backend/services/authority_router.py` | N/A | Complete | Critical |
| Budget source attribution URL | — | `road_infrastructure.data_source_url` in DB and UI cards | N/A | Partially wired | High |

## 25. Runtime policies, thresholds, safety rules, and quality gates from the docs

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| Conversation memory (last 6 turns) | — | `chatbot_service/memory/redis_memory.py` | N/A | Complete | Medium |
| 24-hour conversation TTL | — | `chatbot_service/memory/redis_memory.py` | N/A | Complete | Medium |
| Provider health polling | — | `chatbot_service/providers/router.py` or health worker | N/A | Complete | Medium |
| Circuit breaker open period 60 seconds | — | `chatbot_service/providers/router.py` | N/A | Complete | Medium |
| Provider health dashboard | — | `chatbot_service/api/admin.py` and admin UI | N/A | Complete | Medium |
| Rate limit target | — | `chatbot_service/config.py` and middleware | N/A | Complete | High |
| 500+ Chroma chunks after indexing | — | `chatbot_service/data/build_vectorstore.py` validation | N/A | Complete | High |
| Voice silence auto-stop 5 seconds | — | `frontend/components/chat/VoiceInput.tsx` | N/A | Complete | Medium |
| Voice auto-read speed 0.9 | — | `frontend/components/chat/VoiceOutput.tsx` | N/A | Complete | Medium |
| Crash threshold 2.5G | — | `frontend/lib/crash-detection.ts` | N/A | Complete | High |
| Crash cooldown 30 seconds | — | `frontend/lib/crash-detection.ts` | N/A | Complete | Medium |
| Ignore crash below 10km/h | — | `frontend/lib/crash-detection.ts` | N/A | Complete | High |
| Nearby road issues freshness 90 days | — | backend road issues query layer | N/A | Partially wired | Medium |
| Safety rule: "Call 112 immediately" | — | `chatbot_service/agent/safety_checker.py` | N/A | Complete | High |

## 26. Reference applications and benchmark products mentioned in the docs

These are included so the source material is fully represented, but they are not assets you need to download into the repo.

| Item | Source | Local save path | Env variable name | Status | Priority |
|---|---|---|---|---|---|
| HumSafar Road Safety App | `doc_text.txt` | N/A | N/A | Reference only | Low |
| Rakshak | `doc_text.txt` | N/A | N/A | Reference only | Low |
