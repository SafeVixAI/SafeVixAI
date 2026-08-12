# Data Sources Reference

The SafeVixAI Chatbot relies on high-quality, authoritative data for legal, emergency, and medical accuracy.

```mermaid
flowchart LR
    subgraph Sources[" Data Sources "]
        GEO["Geographic & Routing<br/>Nominatim, OSRM, Photon, OpenCage"]
        EM["Emergency & Location<br/>What3Words, Overpass, Healthsites"]
        ENV["Environment<br/>Open-Meteo, OpenWeatherMap"]
        LEGAL["Legal<br/>MV Act 1988, 2019, State Amendments"]
        MED["Medical<br/>WHO Guidelines, Open FDA"]
    end

    subgraph Tools[" Agent Tools "]
        SOS[SosTool]
        CH[ChallanTool]
        LS[LegalSearchTool]
        FA[FirstAidTool]
        WT[WeatherTool]
        RI[RoadIssuesTool]
    end

    subgraph Engine[" ChatEngine "]
        CA[ContextAssembler]
        PR[ProviderRouter]
        LLM[LLM Provider]
    end

    GEO --> SOS
    EM --> SOS
    ENV --> WT
    LEGAL --> LS
    LEGAL --> CH
    MED --> FA
    SOS --> CA
    CH --> CA
    LS --> CA
    FA --> CA
    WT --> CA
    RI --> CA
    CA --> PR
    PR --> LLM
    LLM --> USER[User Response]

    style Sources fill:#1f6feb,color:#fff
    style Tools fill:#238636,color:#fff
    style Engine fill:#9e6a03,color:#fff


    classDef edge fill:#dbeafe,stroke:#3b82f6,stroke-width:2px,color:#1e3a5f
    classDef control fill:#dcfce7,stroke:#22c55e,stroke-width:2px,color:#14532d
    classDef ai fill:#f3e8ff,stroke:#a855f7,stroke-width:2px,color:#581c87
    classDef data fill:#fef3c7,stroke:#f59e0b,stroke-width:2px,color:#78350f
    classDef security fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,stroke-dasharray:5 5,color:#334155
    classDef decision fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b

    class Sources neutral
    class GEO ai
    class EM success
    class ENV neutral
    class LEGAL neutral
    class MED edge
    class Tools neutral
    class SOS neutral
    class CH neutral
    class LS neutral
    class FA ai
    class WT neutral
    class RI neutral
    class Engine control
    class CA neutral
    class PR neutral
    class LLM ai
    class USER neutral```

## Geographic & Routing Data
- **Nominatim (OpenStreetMap)**: Free, primary reverse geocoding to find road and city names from coordinates.
- **OpenCage**: Standby geocoding fallback, optimizing address resolution for tier-2 Indian cities (requires `OPENCAGE_API_KEY`).
- **BigDataCloud**: Free, client-side reverse geocoding API to resolve coordinates natively in the browser without backend exposure.
- **Photon (Komoot)**: Search autocomplete, heavily biased towards Indian locations using strict bounding box configurations.
- **OSRM (Open Source Routing Machine)**: Free, open-source routing API to generate driving navigation polyline traces.

## Emergency & Location Services
- **What3Words**: High-precision 3-word coordinate resolution (e.g., `///filled.count.soap`) to ensure unambiguous emergency dispatch (requires `W3W_API_KEY`).
- **ip-api.com**: IP-based state and city detection used primarily to enforce dynamic regulatory defaults for legal computations.
- **Overpass API**: Primary engine for querying nearby hospitals, police stations, and fire stations dynamically based on user radius thresholds.
- **Healthsites.io**: Global health facility registry providing supplemental hospital and trauma center seed data via manual extraction pipelines.

## Environment & Context
- **Open-Meteo**: Free, unlimited weather API providing current risk-factors including precipitation probability and visibility.
- **OpenWeatherMap**: Standby fallback for environmental risks, ensuring continuous weather insights (requires `OPENWEATHER_API_KEY`).

## Legal Data
- **Motor Vehicles Act 1988**: Full text, all 217 sections indexed for the RAG pipeline.
- **Motor Vehicles Amendment Act 2019**: Complete gazette notification included.
- **State-specific Amendments**: PDFs indexed for state-level geo-fenced fine queries.
- **MoRTH**: Monitored monthly for updated traffic regulation notifications.

## Medical Data (First Aid)
- **WHO Trauma Care Guidelines**: Official first-aid procedures for emergency response.
- **Open FDA API**: Pharmaceutical lookup referencing official FDA drug labels to evaluate indications and dosages interactively.
- **Static Knowledge base**: `first_aid.json` containing 20 pre-bundled articles for offline RAG capability.

## Real-Time Data Injection
On every message, context is enriched with:
- **GPS Coordinates**: User's current location (lat, lon).
- **Reverse Geocoding**: City and state name for local regulation lookup (via Nominatim/OpenCage).
- **What3Words**: 3-word location summary appended to SOS requests.
- **Road Condition Events**: Recent incidents within a 5km radius of the user.
