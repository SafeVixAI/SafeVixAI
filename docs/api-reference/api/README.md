# API Documentation

Interactive API documentation for SafeVixAI services, generated from OpenAPI specifications.

## Structure

```
docs/api/
â"œâ"€â"€ backend.md         # Backend API reference (Swagger UI)
â"œâ"€â"€ chatbot.md         # Chatbot Service API reference (Swagger UI)
â"œâ"€â"€ changelog.md       # Auto-generated OpenAPI diff history
â""â"€â"€ README.md          # This file
```

## Quick Links

- **Backend API** (`:8000`): 86+ endpoints covering emergency, challan, roadwatch, civic intel, auth, tracking, and administration
- **Chatbot API** (`:8010`): 14+ endpoints for chat, streaming, speech, and health

## Specification Files

The OpenAPI JSON specs live alongside the code:
- `backend/data/openapi.json`
- `chatbot_service/data/openapi.json`

These are generated at build time and referenced by the Swagger UI widgets in `backend.md` and `chatbot.md`.
