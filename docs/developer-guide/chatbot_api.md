# API Reference — Chatbot Service (Port 8010)

The Chatbot Service exposes FastAPI endpoints for AI interaction, retrieval, and health monitoring.

Auto-generated Swagger docs: `http://localhost:8010/docs`

## Endpoint: `GET /health`
- **Description**: Returns service health status and configuration info.
- **Response**: `{"status": "ok", "providers_available": 7, "vectorstore_loaded": true}`

## Endpoint: `POST /api/v1/chat/`
- **Description**: Main chatbot interaction point. Receives user input, classifies intent, runs agent tools, and generates a grounded response.
- **Request Body**:
  - `message`: User input string.
  - `lat`: User's latitude (for location-aware tools).
  - `lon`: User's longitude.
  - `session_id`: Unique session identifier for conversation memory.
  - `language`: Optional language code (auto-detected if not provided).
- **Response**: JSON with assistant text, detected intent, sources, provider used, and latency.

## Endpoint: `POST /api/v1/chat/stream`
- **Description**: Streaming chat interface. Returns tokens as they are generated for low-latency display.
- **Request Body**: Same as `/api/v1/chat/`.
- **Response**: Server-Sent Events stream of tokens.

## Endpoint: `GET /api/v1/chat/history/{session_id}`
- **Description**: Returns conversation history for a session from Redis memory.
- **Response**: Array of message pairs (user + assistant).

## Endpoint: `POST /speech/translate`
- **Description**: Transcribes and translates audio input using IndicSeamless speech model (ai4bharat/indic-seamless).
- **Note**: This endpoint is at `/speech/translate`, NOT `/api/v1/speech/translate`.
- **Request**: Multipart form data with audio file.
- **Response**: `{"text": "transcribed text", "language": "hi"}`

## Endpoint: `GET /speech/status`
- **Description**: Returns the current status of the speech translation service.
- **Response**: `{"available": true, "model": "ai4bharat/indic-seamless", "languages": 14}`

## Endpoint: `GET /api/v1/admin/provider-health`
- **Description**: Returns the current health status of all configured LLM providers.
- **Response**: Object mapping provider names to availability status.
