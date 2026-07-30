# Escalation Procedure

## On-Call Rotation

Currently: **No formal on-call rotation** (project is volunteer-maintained).

For critical incidents, use the following escalation path:

## Escalation Levels

### Level 1: First Responder
- Whoever is available on GitHub / Discord
- Goal: Acknowledge, triage, mitigate if possible
- Time: Within severity SLA

### Level 2: Core Contributor
- For incidents requiring code changes or infrastructure access
- Contact via GitHub @mention or security email
- Time: Within 2 hours of Level 1 escalation

### Level 3: Project Lead
- For P0 incidents, security breaches, or decisions requiring project-wide authority
- Contact via security@safevixai.gov.in
- Time: Within 1 hour of Level 2 escalation

## Contact Channels

| Channel | Purpose | SLA |
|---------|---------|-----|
| GitHub Issues | Bug reports, feature requests | 1-2 business days |
| GitHub Security Advisories | Vulnerability reports | 48 hours |
| security@safevixai.gov.in | Security emergencies | 48 hours acknowledgment |

## Incident Response Steps

1. **Acknowledge** — Confirm receipt within severity SLA
2. **Triage** — Determine severity (P0-P4), assign owner
3. **Mitigate** — Apply hotfix, rollback, or workaround
4. **Resolve** — Deploy permanent fix
5. **Post-mortem** — Document root cause, prevention, timeline

See individual runbooks in `docs/runbooks/` for detailed procedures.
