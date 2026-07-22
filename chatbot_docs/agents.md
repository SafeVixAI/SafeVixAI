# Agent Specialization Overview

The SafeVixAI Chatbot operates as a unified interface but adapts its persona and tools dynamically according to the user's current context: Emergency (SafeVixAI), Legal (DriveLegal), or Infrastructure (RoadWatch).

## Unified Agent Interface
- **Brain**: Driven by the **ProviderRouter** — 10 LLM providers with automatic fallback.
- **Orchestration**: Managed by a custom `ChatEngine` class (`agent/graph.py`).
- **Tools**: 13 distinct tools specialized for different domains.
- **Language**: Auto-detection via Unicode script range regex routes Indian languages to **Sarvam AI** (30B/105B) — separate path from main fallback chain.

## Specialized Agent Personas

### 1. SafeVixAI — Emergency Navigator
Focused on critical life-saving tasks. It prioritizes nearby service location and first-aid instructions.
- **Key Tools**: `SosTool`, `FirstAidTool`, `WeatherTool`, `EmergencyTool`.
- **Knowledge Base**: WHO Trauma Care Guidelines, PostGIS emergency data.
- **Safety Rule**: Any injury mention → response starts with "Call 112 immediately."

### 2. DriveLegal — Traffic Law Expert
A high-authority legal assistant designed to provide accurate fine and regulation info.
- **Key Tools**: `ChallanTool`, `LegalSearchTool`, `EmergencyTool`.
- **Knowledge Base**: Motor Vehicles Act (1988, 2019), state gazette notifications.
- **Precision**: Fine amounts use deterministic DuckDB SQL — never LLM-generated.

### 3. RoadWatch — Infrastructure Guide
Empowers citizens to monitor and report road conditions. Acts as a bridge to road authorities.
- **Key Tools**: `RoadInfrastructureTool`, `RoadIssuesTool`, `SubmitReportTool`, `OpenMeteoTool`.
- **Knowledge Base**: PMGSY/NHAI project data, community incident reports.

## Intent-Based Persona Switching
The chatbot dynamically switches personas using a rule-based `IntentDetector` (`agent/intent_detector.py`). This uses keyword matching and regex patterns — no separate LLM call — ensuring the correct system prompt and context are applied instantly.

| Intent | Persona |
|--------|---------|
| `FIND_HOSPITAL`, `FIND_AMBULANCE`, `FIND_POLICE`, `FIND_TOW` | SafeVixAI |
| `FIRST_AID_INFO` | SafeVixAI |
| `CHALLAN_QUERY`, `LEGAL_INFO` | DriveLegal |
| `ROAD_REPORT` | RoadWatch |
| `OTHER` | General Assistant |
