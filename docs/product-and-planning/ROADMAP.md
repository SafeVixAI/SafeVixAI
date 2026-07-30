# SafeVixAI Roadmap

> **Last updated:** 2026-07-29

## Completed Phases

```mermaid
flowchart LR
    subgraph Completed["Completed Phases"]
        direction LR
        P0["Phase 0<br/>Audit & P0 Fixes<br/>Jun 2026"]
        P1["Phase 1<br/>Route Tests<br/>+ Coverage<br/>Jun 2026"]
        P2["Phase 2-4<br/>Lib Tests<br/>+ Hardening<br/>Jun 2026"]
        P5["Phase 5<br/>Code Quality<br/>CQRS, Redlock<br/>Jun 2026"]
        P6["Phase 6<br/>CI Integration<br/>Hypothesis, SW<br/>Jul 2026"]
        P7["Phase 7<br/>DDD & Ubiquitous<br/>Language<br/>Jul 2026"]
        P8["Phase 8<br/>Monitoring<br/>+ Observability<br/>Jul 2026"]
        P9["Phase 9<br/>Enterprise Lock<br/>100% Coverage<br/>Jul 2026"]
    end

    P0 --> P1 --> P2 --> P5 --> P6 --> P7 --> P8 --> P9
```

## 12-Month Roadmap

```mermaid
gantt
    title SafeVixAI 12-Month Roadmap
    dateFormat  YYYY-MM-DD
    axisFormat  %Y Q%q

    section Q3 2026 — v1.1
    OpenSSF Silver Badge          :2026-07-01, 2026-09-30
    i18n Full (14 languages)      :2026-08-01, 2026-09-30
    Offline SOS Queue Polish      :2026-07-15, 2026-08-15
    E2E Test Stabilization        :2026-08-01, 2026-09-15

    section Q4 2026 — v1.2
    Bystander Mode V2             :2026-10-01, 2026-12-31
    Crash Detection GA            :2026-10-15, 2026-12-15
    Voice AI (IndicSeamless)      :2026-11-01, 2026-12-31
    Performance Budgets (LH 90+)  :2026-10-01, 2026-11-30

    section Q1 2027 — v1.3
    Terraform Infrastructure      :2027-01-01, 2027-03-31
    Penetration Testing            :2027-02-01, 2027-03-15
    DPDP Compliance Audit         :2027-01-15, 2027-03-01
    Sentry Error Triage Dashboard :2027-02-15, 2027-03-31

    section Q2 2027 — v2.0
    Multi-Region Deployment       :2027-04-01, 2027-06-30
    Community Incident Reports    :2027-04-15, 2027-06-01
    WebSocket Live Tracking GA    :2027-05-01, 2027-06-30
    Kubernetes Production Ready   :2027-04-01, 2027-06-30
```

---

## Completed (Initial Release)

- **Phase 1-6:** All core features built and hardened — see [`docs/Roadmap.md`](docs/Roadmap.md) for full build history.
- **25/25 Features:** Emergency Locator, AI Chatbot RAG, Challan Calculator, Road Reporter, Offline Mode, PWA, Voice/ASR, Live Tracking, and more.
- **OpenSSF Best Practices Badge:** Passing tier achieved (Silver in progress).

---

## Next 12 Months (2026 Q3 - 2027 Q2)

### Q3 2026 (Jul-Sep)
| Milestone | Details |
|-----------|---------|
| v1.1 Release | Bug fixes, performance improvements, accessibility audit |
| OpenSSF Silver Badge | Complete all Silver criteria: threat model, security requirements, 80% coverage |
| Accessibility Pass | WCAG 2.1 AA compliance audit and fixes |
| i18n Expansion | Add Tamil, Hindi, Telugu UI translations (beyond existing speech support) |
| Load Testing Results | Publish k6 benchmarks and capacity planning guide |

### Q4 2026 (Oct-Dec)
| Milestone | Details |
|-----------|---------|
| v1.2 Release | New features from community feedback |
| OpenSSF Gold Badge | Complete reproducible builds, branch coverage >=80%, CI integration |
| Crash Detection Refinement | Accelerometer-based detection with fewer false positives |
| Bystander Mode V2 | Real-time incident sharing, witness coordination |
| Offline AI v2 | WebLLM model quantization for faster local inference |

### Q1 2027 (Jan-Mar)
| Milestone | Details |
|-----------|---------|
| v1.3 Release | Enterprise features, API stability guarantee |
| Terraform GA | Infrastructure-as-Code for production AWS deployment |
| Penetration Test | Third-party security audit |
| Performance Budget | Lighthouse scores >=90 across all categories |

### Q2 2027 (Apr-Jun)
| Milestone | Details |
|-----------|---------|
| v2.0 Release | Major release with breaking API changes if needed |
| Multi-Region Support | EU data residency option for GDPR compliance |
| Community Growth | 20+ external contributors, 500+ GitHub stars |
| Sustainability Report | Infra cost analysis, funding strategy, grant applications |

---

## How to Contribute

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for contribution guidelines and [`TESTING_POLICY.md`](TESTING_POLICY.md) for test requirements.

---

## Feature Requests

Submit feature requests via [GitHub Issues](https://github.com/SafeVixAI/SafeVixAI/issues/new/choose) using the feature request template.
