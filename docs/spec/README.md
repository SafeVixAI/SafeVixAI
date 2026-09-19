# SafeVixAI Technical Specifications (SPEC)

> **Authority:** Authoritative & Binding  
> **Audience:** Core Engineers, System Architects, Compliance Auditors, CI Automation, AI Agents  
> **Status:** Production Normative (v1.0.0-STABLE)

---

## 1. Governance & Specification Contract

Documents contained within this `spec/` hierarchy constitute the **authoritative, normative contracts** of the SafeVixAI platform. Unlike the narrative documentation in `docs/`, specifications define:
- **System Invariants:** Architectural constraints that code, PRs, and refactors MUST NOT violate.
- **Interface & Data Contracts:** Exact API schemas, database models, error code catalogs, and webhook payloads.
- **Security & Privacy Baselines:** Cryptographic standards, role-based access control (RBAC) boundaries, and DPDP Act / GDPR data processing limits.
- **Engineering Quality Gates:** Measurable test coverage thresholds, code hygiene rules, and performance SLA benchmarks.

Any change to a specification requires an approved **Architecture Decision Record (ADR)** or formal RFC approval from the Project Maintainers.

---

## 2. Specification Directory Structure

```text
spec/
├── api/                           # API & Interface Contracts
│   ├── error_codes.spec.md        # Canonical Error Codes Catalog (AUTH001..SOS008)
│   ├── circuit_breaker.spec.md    # Circuit Breaker & Resilience State Machine Spec
│   └── webhooks.spec.md           # Outbound Event Payload & HMAC Signature Contract
│
├── architecture/                  # Architectural Invariants & Decisions
│   ├── adr/                       # ADR-001 through ADR-012 (Canonical ADRs)
│   └── offline_engine.spec.md     # 7-Layer Offline PWA Progressive Enhancement Contract
│
├── data/                          # Data Models & Schemas
│   ├── database_schema.spec.md    # Canonical PostGIS 16 Schema (23 ORM Tables)
│   ├── dataset_placement.spec.md  # Raw Data Ingestion & Asset Placement Conventions
│   └── civic_intel.spec.md        # Civic Intel, Boundary & OSM Spatial Asset Specifications
│
├── domain/                        # Core Domain Specifications
│   ├── notifications.spec.md      # Multi-Channel Notification Routing & Invariants
│   └── plugin_system.spec.md      # Dynamic Plugin Lifecycle & Extension Contract
│
├── ai/                            # AI & Chatbot Behavior Specifications
│   ├── fallback_chain.spec.md     # 10-Provider LLM Fallback & Circuit Breaker Contract
│   ├── tools_matrix.spec.md       # 12 Chatbot Agent Tools & Parameter Contracts
│   ├── personas.spec.md           # Agent Persona Definitions & Context Prompts
│   ├── rag_vectorstore.spec.md    # LocalHashEmbedding & ChromaDB Contract
│   └── prompt_safety.spec.md      # L1/L2 Harm Classification & Safety Guardrails
│
├── security/                      # Security & Regulatory Specifications
│   ├── authentication.spec.md     # JWT HS256 & Supabase Auth Contract (24h TTL)
│   ├── rbac_matrix.spec.md        # 5-Role Access Control Matrix (admin..readonly)
│   ├── threat_model.spec.md       # STRIDE Threat Vectors & Mitigations
│   ├── privacy_boundary.spec.md   # DPDP Act 2023 & GDPR Data Boundary Contract
│   ├── security_requirements.spec.md # Enterprise Security Controls & Invariants
│   ├── gdpr_compliance.spec.md    # GDPR Articles 9, 15, 17, 30 Compliance Specification
│   ├── hipaa_compliance.spec.md   # Emergency Medical Data Protection Specification
│   ├── soc2_compliance.spec.md    # Trust Services Criteria Controls Specification
│   └── telemetry_privacy.spec.md  # Telemetry Collection Limits & PII Scrubbing
│
└── engineering/                   # Engineering & Quality Standards
    ├── testing_policy.spec.md     # Coverage Thresholds (86/71/80/84) & Test Pyramid
    ├── code_standards.spec.md     # PEP 8, Ruff & TypeScript Strict Standards
    ├── env_validation.spec.md     # Environment Variable Schema & Validation Rules
    ├── env_configuration.spec.md  # Service Environment Variable Reference Contract
    ├── slo.spec.md                # Platform SLOs, SLIs, & Error Budget Allocations
    ├── supported_versions.spec.md # Platform Version Support & Deprecation Policy
    ├── versioning_policy.spec.md  # SemVer 2.0.0 Rules & Release Cadence
    ├── performance_benchmarks.spec.md # Latency & Throughput Acceptance Criteria
    └── wcag_compliance.spec.md    # WCAG 2.1 AA Accessibility Contract
```

---

## 3. Single Sources of Truth (SSOT) Map

| System Domain | Authoritative Spec Document | Enforcing Code / Implementation |
| :--- | :--- | :--- |
| **RBAC Roles & Permissions** | [`docs/spec/security/rbac_matrix.spec.md`](security/rbac_matrix.spec.md) | `backend/core/rbac.py` |
| **Authentication & Tokens** | [`docs/spec/security/authentication.spec.md`](security/authentication.spec.md) | `backend/core/security.py` |
| **Database Schema** | [`docs/spec/data/database_schema.spec.md`](data/database_schema.spec.md) | `backend/models/*.py`, Alembic migrations |
| **Error Codes** | [`docs/spec/api/error_codes.spec.md`](api/error_codes.spec.md) | `backend/core/exceptions.py`, `error_codes.py` |
| **Circuit Breakers** | [`docs/spec/api/circuit_breaker.spec.md`](api/circuit_breaker.spec.md) | `backend/core/circuit_breaker.py` |
| **LLM Fallback Chain** | [`docs/spec/ai/fallback_chain.spec.md`](ai/fallback_chain.spec.md) | `chatbot_service/providers/` |
| **Agent Tool Matrix** | [`docs/spec/ai/tools_matrix.spec.md`](ai/tools_matrix.spec.md) | `chatbot_service/tools/` |
| **Test Coverage & Quality** | [`docs/spec/engineering/testing_policy.spec.md`](engineering/testing_policy.spec.md) | `frontend/jest.config.js`, `pytest.ini` |
| **DPDP & Privacy Boundaries**| [`docs/spec/security/privacy_boundary.spec.md`](security/privacy_boundary.spec.md) | `backend/models/user.py`, `services/encryption.py` |
