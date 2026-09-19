# GDPR Compliance Specification (SPEC)

> **Authority:** Authoritative Compliance Specification  
> **Regulation:** General Data Protection Regulation (Regulation (EU) 2016/679)  
> **Status:** Production Normative (v1.0.0-STABLE)

---

## 1. Scope & Applicability

This specification establishes SafeVixAI's technical compliance controls under the EU General Data Protection Regulation (GDPR) for cross-border travelers, European tourists, and international road users operating within jurisdictions covered by SafeVixAI services.

---

## 2. Article-by-Article Implementation Controls

### 2.1 Article 5 — Principles Relating to Processing of Personal Data
- **Data Minimization (Art. 5(1)(c)):** Telemetry and traffic flow monitoring do not collect personally identifiable information (PII). IP addresses are hashed with daily rotating salts before being written to logs.
- **Accuracy (Art. 5(1)(d)):** Citizens can directly inspect, update, and correct their personal profile data via `PATCH /api/v1/users/profile`.
- **Storage Limitation (Art. 5(1)(e)):** High-frequency GPS tracking streams are deleted after an SOS dispatch or route navigation session is marked `resolved` (maximum TTL: 7 days).

### 2.2 Article 9 — Processing of Special Categories of Personal Data (Health & Medical Data)
- **Medical & Blood Group Data:** Citizen blood group, allergies, and emergency medical notes constitute special category health data under Art. 9(1).
- **Lawful Exception (Art. 9(2)(c) — Vital Interests):** Processing of emergency contacts and medical data is legally grounded in protecting the vital interests of the data subject during life-threatening emergency road incidents.
- **Cryptographic Isolation:** Health attributes in `backend/models/user.py` are encrypted at rest with AES-256 and only decrypted during an active dispatch.

### 2.3 Article 15 — Right of Access
- Citizens can export a full JSON bundle of all personal data held by SafeVixAI using `GET /api/v1/users/export`.

### 2.4 Article 17 — Right to Erasure ("Right to be Forgotten")
- Citizens can execute an irreversible account and profile erasure using `DELETE /api/v1/users/profile`.
- Erases user records across `user_profiles`, IndexedDB client store, and revokes active JWT sessions.

### 2.5 Article 32 — Security of Processing
- All client-to-server and inter-service communications enforce TLS 1.3 with mandatory PFS (Perfect Forward Secrecy).
- Role-based access control enforces least privilege across operators, officers, and administrators.
