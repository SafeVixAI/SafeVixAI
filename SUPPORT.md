# SafeVixAI Support

## Support Workflow

```mermaid
flowchart TB
    START["User Has an Issue"] --> PRE{"Check existing resources"}

    PRE -->|Search issues| GI["GitHub Issues"]
    PRE -->|Read docs| DOC["Setup / Deployment / FAQ"]
    PRE -->|Search closed| CI["Closed issues"]

    GI --> FOUND{"Found solution?"}
    DOC --> FOUND
    CI --> FOUND

    FOUND -->|Yes| RESOLVED["Issue Resolved"]
    FOUND -->|No| TYPE{"Issue Type?"}

    TYPE -->|Bug| BUG["Open Bug Report"]
    TYPE -->|Feature Request| FR["Open Feature Request"]
    TYPE -->|Security| SEC["Email security@safevixai.gov.in"]
    TYPE -->|Question| DISC["GitHub Discussions"]

    BUG --> SLA["Response: 1-2 business days"]
    FR --> SLA2["Response: 1-3 business days"]
    SEC --> SLA3["Response: 48-hour acknowledgement"]
    DISC --> SLA4["Response: 1-3 business days"]

    classDef neutral fill:#f8fafc,stroke:#64748b,stroke-width:2px,color:#1e293b
    classDef check fill:#e0e7ff,stroke:#6366f1,stroke-width:2px,color:#312e81
    classDef action fill:#fff7ed,stroke:#f97316,stroke-width:2px,color:#7c2d12
    classDef success fill:#d1fae5,stroke:#10b981,stroke-width:2px,color:#064e3b
    classDef critical fill:#fee2e2,stroke:#ef4444,stroke-width:2px,color:#7f1d1d
    classDef external fill:#f1f5f9,stroke:#94a3b8,stroke-width:2px,color:#334155

    class START neutral
    class PRE,FOUND,TYPE check
    class GI,DOC,CI,BUG,FR,DISC action
    class RESOLVED success
    class SEC,SLA3 critical
    class SLA,SLA2,SLA4 external
```

## Community Support (Free)

| Channel | Where | Typical Response Time |
|---------|-------|----------------------|
| GitHub Issues | [github.com/SafeVixAI/SafeVixAI/issues](https://github.com/SafeVixAI/SafeVixAI/issues) | 1-2 business days |
| GitHub Discussions | [github.com/SafeVixAI/SafeVixAI/discussions](https://github.com/SafeVixAI/SafeVixAI/discussions) | 1-3 business days |

## Security Issues

Do **not** open a public GitHub issue. See [SECURITY.md](SECURITY.md) for responsible disclosure.

**Contact:** `safevixai@googlegroups.com` — 48-hour acknowledgement SLA.

## Bug Reports

1. Search [existing issues](https://github.com/SafeVixAI/SafeVixAI/issues) first
2. Use the bug report template (`ISSUE_TEMPLATE/bug_report.md`)
3. Include: environment, steps to reproduce, expected vs actual behavior, logs/screenshots

## Feature Requests

1. Search [existing issues](https://github.com/SafeVixAI/SafeVixAI/issues) first
2. Use the feature request template (`ISSUE_TEMPLATE/feature_request.md`)
3. Describe the problem, proposed solution, and alternatives considered

## Before Asking

- Read [SETUP.md](docs/developer-guide/SETUP.md) for installation issues
- Read [docs/Deployment.md](docs/developer-guide/chatbot/deployment.md) for deployment issues
- Check [docs/TechStack.md](docs/architecture/TechStack.md) for version compatibility
- Search closed issues for solutions

## Service Status

- Frontend: [safevixai.vercel.app](https://safevixai.vercel.app)
- Backend API: [safevixai-api.onrender.com/docs](https://safevixai-api.onrender.com/docs)
- Status page: TBD
