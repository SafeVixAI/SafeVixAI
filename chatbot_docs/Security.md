# Security and Safety — SafeVixAI Chatbot

Since the SafeVixAI Chatbot operates in emergency and legal contexts, security and safety are non-negotiable.

## Safety Check Pipeline
The `ChatEngine` includes a mandatory `SafetyChecker` node (`agent/safety_checker.py`):
- **Pre-check**: Evaluates user input before processing — blocks harmful or manipulative queries using 12-pattern prompt injection guard.
- **Post-check**: If a response is for an emergency query (injury, accident, trauma), validates the content.
- **Rule**: Ensures that at least one emergency number (112) and a nearby hospital's contact information are included in emergency responses.
- **Action**: If a response fails this check, it's flagged and a retry is initiated with a different provider.
- **Governance**: All safety events are logged via `governance.py` for audit trail.

## LLM Provider Security
- **API Keys**: All keys are stored in environment variables (`.env`), never in code or committed to Git.
- **Fallback Logic**: 10 providers in fallback chain + Sarvam Indian language path ensure that downtime on one platform doesn't affect the user.
- **Rate Limiting**: Users are capped at 30 messages per session per hour to prevent abuse while ensuring availability for legitimate emergencies.
- **Provider Isolation**: Each provider has its own SDK wrapper — a vulnerability in one doesn't cascade.

## Data Privacy
- **Anonymous Sessions**: Usage is tracked by session ID (UUID), reducing the need for persistent personal data storage.
- **PII Protection**: User-reported incidents are anonymized before being shared with the broader community through road hazards.
- **Context Handling**: GPS coordinates are used for real-time localization but are not stored in the long-term knowledge base.
- **IndexedDB Only**: Blood group, allergies, and emergency contacts are stored only in the browser's IndexedDB — never uploaded to any server.

## Content Filtering
- **Factual Reliance**: The RAG pipeline ensures that legal and medical responses are grounded in verified sources (Motor Vehicles Act and WHO guidelines) rather than model hallucinations.
- **Deterministic Fines**: Traffic fine amounts always come from DuckDB SQL queries against `violations_seed.csv` — never LLM-generated.
- **Fallbacks**: If the retriever confidence is low (below min_score=0.55), the chatbot is instructed to refer the user to official sources like 112 and 1033.
