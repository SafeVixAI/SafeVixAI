# SOC 2 Type II Security & Trust Services Criteria Specification (SPEC)

> **Authority:** Authoritative Compliance Specification  
> **Framework:** AICPA SOC 2 Type II Trust Services Criteria (Security, Availability, Confidentiality)  
> **Status:** Production Normative (v1.0.0-STABLE)

---

## 1. Common Criteria (Security)

### CC6.1 — Logical Access Controls
- System access is restricted via 5-role RBAC (`backend/core/rbac.py`).
- Passwords are encrypted using Argon2id / bcrypt with salt rounds >= 12.
- Session tokens enforce 24-hour expiration (`ACCESS_TOKEN_EXPIRE_HOURS=24`).

### CC6.6 — Boundary Protection & Network Security
- All edge endpoints are protected by Cloudflare WAF, TLS 1.3 termination, and rate limiting (HTTP 429).
- Database ports (5432) and Redis ports (6379) are isolated within private VPC subnets with zero public ingress.

### CC7.2 — Vulnerability Management & CI Pipelines
- Automated security scanning runs in GitHub Actions:
  - CodeQL static application security testing (SAST).
  - Dependency vulnerability scanning (`pip-audit`, `npm audit`).
  - Container image vulnerability scanning and Cosign cryptographic signing.

---

## 2. Availability Criteria (A1.1 — A1.3)

- **99.9% Uptime Target:** Service architecture features multi-provider fallback chains for LLMs (10 providers), multi-replica deployment on Kubernetes, and Redis Sentinel caching.
- **Automated Failover:** Database failover and degraded read-only routing via PostGIS replica pools.
