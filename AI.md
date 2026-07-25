# AI Capabilities
> Version 1.0 | 2026-07-25

## Chatbot Architecture
User Message → SafetyChecker → IntentDetector (9 classes) → ContextAssembler (13 tools) → ProviderRouter (10 providers) → ConversationMemoryStore (Redis, 24h TTL) → ChatResponse

## 9 Intent Classes
- emergency (accident, ambulance, police, SOS)
- first_aid (bleeding, CPR, fracture, burn)
- challan (fine, helmet, seatbelt, drunk driving)
- legal (motor vehicles act, right of way)
- road_report (pothole, repair, streetlight)
- bystander (witness, report incident)
- weather (rain, road conditions)
- general_query (fallback)
- offline (Phi-3 Mini when no connectivity)

## 10-Provider Fallback Chain
Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together → Sarvam (Indic) → Template (deterministic)

## 13 Agent Tools
SosTool, EmergencyTool, ChallanTool, LegalSearchTool, FirstAidTool, WeatherTool, OpenMeteoTool, RoadInfrastructureTool, RoadIssuesTool, SubmitReportTool, GeocodingClient, DrugInfoTool, What3WordsTool

## Safety
12 injection pattern guards. Medical responses always begin "Call 112 immediately".

## Offline AI
- Phi-3 Mini 2.2GB (4-bit) for browser inference
- YOLOv8n 15MB ONNX for pothole detection
- DuckDB-Wasm ~5MB for offline challan calculation
- 20 WHO first-aid articles in HNSW index
