# Frequently Asked Questions

## General

### What is SafeVixAI?
SafeVixAI is an AI-powered road safety PWA built for the IIT Madras Road Safety Hackathon 2026. It combines an Emergency Locator, AI Chatbot, Challan Calculator, and Road Reporter in a single offline-first Progressive Web App.

### Is SafeVixAI free?
Yes. SafeVixAI is 100% free and open source under the MIT License. Total infrastructure cost is ₹0 — all services use free tiers.

### Who built SafeVixAI?
The SafeVixAI Team — a submission team for the IIT Madras Road Safety Hackathon 2026.

## Installation

### How do I set up SafeVixAI locally?
See [SETUP.md](SETUP.md) for step-by-step instructions for all three services (backend, chatbot, frontend). The quick start requires Python 3.11+, Node.js 20+, and Git.

### Do I need a database?
For full functionality, you need PostgreSQL with PostGIS. For development, the Docker Compose setup provides both PostgreSQL and Redis automatically.

### Do I need API keys?
Some features require API keys: LLM providers (Groq, Gemini, etc.) for the chatbot, OpenWeather for weather data, and What3Words for location resolution. See `backend/.env.example` and `chatbot_service/.env.example` for the full list.

## Usage

### Does SafeVixAI work offline?
Yes. Core features work offline:
- **Emergency Locator**: Cached data for 25 Indian cities
- **AI Chatbot**: Phi-3 Mini runs in-browser via WebLLM
- **Challan Calculator**: DuckDB-Wasm runs SQL client-side
- **Road Reporter**: Reports queued in IndexedDB, sent when online

### How does the SOS feature work?
Press and hold the SOS button for 2 seconds. Your GPS location is shared with emergency contacts via SMS/WhatsApp. Family members can track your location in real time via a WebSocket stream.

### What LLM providers are supported?
9 providers in fallback chain: Groq → Cerebras → Gemini → GitHub Models → NVIDIA NIM → OpenRouter → Mistral → Together AI → Template (deterministic fallback).

## Development

### How do I run tests?
```bash
# Frontend
cd frontend && npm test

# Backend
cd backend && pytest tests/

# Chatbot
cd chatbot_service && pytest tests/
```

### How do I contribute?
See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution workflow, coding standards, and PR checklist.

## Troubleshooting

### The build takes too long
If `npm run build` takes 10+ minutes, you likely have `STANDALONE=true` set. Use the default build (without STANDALONE) for faster iteration, or see [SETUP.md](SETUP.md) for details.

### Tests fail with "Cannot find namespace 'React'"
This is a pre-existing Next.js 15 generated-types issue. See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for the workaround.

### Where can I get help?
Open a [GitHub Issue](https://github.com/SafeVixAI/SafeVixAI/issues) or start a [GitHub Discussion](https://github.com/SafeVixAI/SafeVixAI/discussions).
