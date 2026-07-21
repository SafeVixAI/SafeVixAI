# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.0.x (current) | ✅ Security patches |
| < 1.0 (pre-release) | ❌ No support |

## Reporting a Vulnerability

**DO NOT file a public GitHub issue for security vulnerabilities.**

Report vulnerabilities to **security@safevixai.gov.in**.

You should receive an acknowledgment within 48 hours. We will work with you to understand the scope, develop a fix, and coordinate disclosure.

### What to include

- Type of issue (XSS, SQLi, RCE, privilege escalation, etc.)
- Full reproduction steps or proof of concept
- Affected component (backend, chatbot, frontend)
- Suggested fix (if available)

### Disclosure Timeline

| Phase | Duration |
|-------|----------|
| Acknowledgment | Within 48 hours |
| Triage & Assessment | 3 business days |
| Fix & Testing | 5-14 business days (depends on severity) |
| Public Disclosure | After fix is released |

We aim to disclose vulnerabilities within 30 days of receiving the report.

## Security Features

### Authentication
- JWT-based authentication (RS256) with JWKS rotation
- Auth tokens never passed in URLs
- Session tokens with configurable TTL

### Data Protection
- Blood group and emergency contacts stored only in IndexedDB (never on server)
- All API traffic over HTTPS/TLS
- Redis connections support TLS (`rediss://`)
- Secrets managed via environment variables (gitignored)

### API Security
- Rate limiting on all endpoints
- CORS restricted to known origins
- Host header validation
- Content-Security-Policy headers
- Request ID tracking for audit trails

### LLM Security
- Prompt injection defense via SafetyChecker
- All LLM output validated for harmful content
- 9-provider fallback chain prevents single-point failure

## Bug Bounty

This project operates on a **responsible disclosure** basis — no bug bounty program is currently offered.

## Contact

- **Security issues:** security@safevixai.gov.in
- **General inquiries:** safevixai@googlegroups.com
