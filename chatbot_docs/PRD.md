# Product Requirements Document (PRD) — SafeVixAI Chatbot

The SafeVixAI AI Chatbot is a core component of the SafeVixAI safety platform, designed to provide real-time, authoritative assistant services for road users in India.

## Problem Statement
Road accidents in India are often followed by critical delays in locating emergency services, lack of legal clarity on traffic fines, and a lack of transparency in infrastructure reporting. Users need an intelligent, high-availability assistant to bridge these gaps.

## Target Audience
- Drivers and commuters on Indian highways.
- First responders and bystanders at accident scenes.
- Citizens interested in road infrastructure transparency.

## User Requirements
- **Immediate Response**: Quick access to nearest hospital and 112 services.
- **Authoritative Data**: Accurate legal information on traffic laws and fines (deterministic, not LLM-generated).
- **Ease of Use**: Hands-free voice interaction for drivers and those in trauma.
- **Local Context**: Personalized info based on GPS (local hospitals, state-specific fines).
- **Indian Languages**: Native support for 14 Indian languages (Hindi, Tamil, Telugu, Kannada, Bengali, etc.) via Sarvam AI.

## System Performance Goals
- **Response Latency**: Under 3 seconds for initial token generation (Groq 300+ tok/s).
- **Availability**: 99.9% uptime through 10-provider LLM fallback chain + Sarvam Indian language path.
- **Accuracy**: Minimal hallucination by strictly using RAG-backed facts (top_k=5, min_score=0.55) and deterministic DuckDB SQL for fines.
- **Multi-language**: Seamless interaction in 14 Indian languages via Sarvam AI auto-routing (Unicode script detection).
- **Offline**: First-aid and basic legal info available via WebLLM Phi-3 Mini when offline.

## Success Metrics
- **Response Utility**: High user ratings (thumbs up) for AI accuracy.
- **Emergency Speed**: Reduction in time taken to locate and call nearest services.
- **Community Growth**: Increase in infrastructure issue reports via the chatbot.

## Test Status
- **Chatbot**: 892/892 tests passing, 95% coverage
- **Backend**: 1365/1365 tests passing
- **Frontend**: 572/572 tests passing
- **E2E**: 45/55 passing
- **Total unit tests**: 2829
