# Privacy Policy
> Version 1.0 | 2026-07-25

## Data Collection
| Data | Storage | Purpose |
|------|---------|---------|
| Email/Phone | PostgreSQL | Account, emergency sharing |
| Location | Transient | Emergency locator |
| Blood group | IndexedDB only | Never leaves device |
| Chat history | Redis (24h TTL) | Conversation continuity |
| Road reports | PostgreSQL (anonymized) | Infrastructure improvement |
| Analytics | PostHog (opt-in) | Product improvement |

## Compliance
- GDPR: Export (`GET /api/v1/user/export`) and delete endpoints
- DPDP Act 2023: Data localization, consent management
- Security headers: CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
