# Security Requirements

> Documented security requirements for SafeVixAI — what users can and cannot expect from this software.

## What Users Can Expect

### Authentication & Identity
- **Authenticated users:** JWT-based auth with 24h access tokens and 30d refresh tokens.
- **Guest users:** Anonymous UUID-based guest identity — no sign-up required for core features.
- **Passwords:** Stored as iterated hashes with per-user salt (Argon2id via passlib).
- **2FA:** Core contributors and maintainers MUST use GitHub 2FA for repository access.

### Data Protection
- **In transit:** All network communication uses TLS 1.2+ (HTTPS, WSS). Service-to-service uses internal API keys.
- **At rest:** Redis chat history has 24h TTL. PostgreSQL database is encrypted at rest (cloud provider managed).
- **Personal data:**
  - Blood group, emergency contacts: stored only in IndexedDB on the user's device — never transmitted to the server.
  - GPS location: processed server-side for emergency services, cached only, not persisted.
  - Chat history: stored in Redis with 24-hour automatic expiry.
  - Session data: JWT claims contain only user UUID and role — no PII in tokens.

### API Security
- **Rate limiting:** Public endpoints throttle at 100 req/min (general), 5/min (auth), 3/min (SOS), 60/min (challan), 30/min (chat and geocode).
- **Input validation:** All API inputs validated via Pydantic schemas — type coercion, bounds checking, file type/size limits.
- **CORS:** Restricted to known origins in production. No wildcard.
- **CSRF:** Protection on all state-changing requests.
- **Host validation:** ALLOWED_HOSTS middleware rejects mismatched Host headers.

### LLM Safety
- **Prompt injection defense:** SafetyChecker evaluates all user messages against 60+ injection patterns (jailbreaks, NFKC normalization bypass, zero-width characters, l33t speak, RAG prompt injection).
- **Injury disclosure:** Any response about injuries MUST begin with "Call 112 immediately."
- **Timeout:** All LLM provider calls enforce `asyncio.wait_for()` with configurable timeout.
- **RAG sanitization:** Retrieved context is sanitized before injection into LLM prompts.

### Vulnerability Management
- **Reporting:** Private vulnerability reporting via email and GitHub Security Advisories.
- **SLA:** Acknowledgment within 48 hours. Critical fixes within 14 days.
- **Disclosure:** Coordinated disclosure — reporters agree to wait for fix release.

## What Users Cannot Expect

- **Perfect security:** No software is 100% secure. We follow industry best practices and respond to reported vulnerabilities promptly.
- **End-to-end encryption:** Chat messages are encrypted in transit (TLS) but decrypted server-side for LLM processing.
- **Formal verification:** The codebase has not undergone formal mathematical verification.
- **Air-gap security:** The service requires network connectivity for most features (offline mode is limited).
- **Regulatory compliance:** While we follow security best practices, we have not undergone formal certification (SOC 2, ISO 27001, etc.).

## Security Boundaries

```mermaid
flowchart TB
    U[User] -->|"Untrusted<br/>TLS, CSP, XSS"| F[Frontend]
    F -->|"Low Trust<br/>JWT, CORS, Rate Limit"| B[Backend]
    B -->|"Medium Trust<br/>Internal API Key, Private Network"| C[Chatbot]
    C -->|"Low Trust<br/>API Keys, Timeouts"| LLM[LLM Providers]
    B -->|"Medium Trust<br/>Network Isolation"| DB[Database]
    B -->|"Medium Trust<br/>Encrypted"| RS[Redis]
    UI[Public Internet] -->|"Untrusted<br/>WAF, DDoS, CSP"| F

    style U fill:#da3633,color:#fff
    style UI fill:#da3633,color:#fff
    style F fill:#1f6feb,color:#fff
    style B fill:#238636,color:#fff
    style C fill:#9e6a03,color:#fff
    style LLM fill:#6e5494,color:#fff
    style DB fill:#238636,color:#fff
    style RS fill:#8957e5,color:#fff


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

    class U neutral
    class F edge
    class B control
    class C ai
    class LLM ai
    class DB data
    class RS data
    class UI neutral```

## Cryptographic Requirements

| Requirement | Implementation | Standard |
|-------------|---------------|----------|
| Password hashing | Argon2id via passlib | NIST SP 800-63B |
| JWT signing | HS256 | RFC 7519 |
| TLS | 1.2+ | NIST SP 800-52 |
| CSPRNG | secrets module (Python) / crypto.getRandomValues (JS) | FIPS 140-2 |
| Key lengths | 256-bit (JWT), 128-bit+ (TLS) | NIST SP 800-57 (2030+) |

## Third-Party Security

SafeVixAI depends on the security of:
- **GitHub** — for repository hosting, CI/CD, container registry, and security advisories.
- **Vercel (Frontend), Render (Backend, Chatbot), Supabase (PostgreSQL), Upstash (Redis)** — cloud infrastructure providers with their own security programs.
- **LLM API providers (Groq, Cerebras, Gemini, etc.)** — user messages are sent to these providers for AI responses.
- **npm/PyPI ecosystems** — dependencies are pinned and scanned for known vulnerabilities.
