# SafeVixAI — Kubernetes

Self-hosted K8s deployment manifests (for bare-metal or non-AWS cloud).

## Directory Structure

```
k8s/
├── kustomization.yaml           # Resource aggregation + patches
├── namespace.yaml               # safevixai namespace
├── priority-class.yaml          # safevixai-high / safevixai-default
├── resource-quota.yaml          # CPU/memory limits per namespace
├── service-account.yaml         # RBAC for each service
├── external-secrets.yaml        # External Secrets Operator (AWS SSM / GCP SM)
├── network-policy.yaml          # Ingress isolation rules
├── backend-config.yaml          # Backend ConfigMap
├── backend-deployment.yaml      # Backend Deployment + Service + HPA
├── chatbot-config.yaml          # Chatbot ConfigMap
├── chatbot-deployment.yaml      # Chatbot Deployment + Service + HPA
├── frontend-config.yaml         # Frontend ConfigMap
├── frontend-deployment.yaml     # Frontend Deployment + Service + HPA
└── ingress.yaml                 # NGINX Ingress (path-based routing)
```

## Services

| Service | Port | Image | Replicas | Priority |
|---------|------|-------|----------|----------|
| `safevixai-backend` | 8000 | `ghcr.io/.../backend:latest` | 2-6 (HPA) | high |
| `safevixai-chatbot` | 8010 | `ghcr.io/.../chatbot:latest` | 2-4 (HPA) | high |
| `safevixai-frontend` | 3000 | `ghcr.io/.../frontend:latest` | 2-4 (HPA) | default |

## Deploy

```bash
# Deploy all resources
kubectl apply -k k8s/

# Deploy single service (after infrastructure is up)
kubectl apply -f k8s/backend-deployment.yaml

# Rollback
kubectl rollout undo deployment/safevixai-backend -n safevixai

# Port-forward (local testing)
kubectl port-forward -n safevixai service/safevixai-backend 8000:8000

# Scale
kubectl scale deployment/safevixai-frontend -n safevixai --replicas=5
```

## Patch Rules (kustomization.yaml)

- Backend + Chatbot get `safevixai-high` priority class (critical for SOS/emergency)
- Frontend gets `safevixai-default` (burstable, less critical)
- All deployments get topology spread constraints (zone-aware scheduling)
- Backend + Chatbot get dedicated service accounts with granular RBAC

## Ingestion Routing (ingress.yaml)

| Host | Path | Service |
|------|------|---------|
| `api.safevixai.gov.in` | `/api/v1/*`, `/ws/*`, `/health` | safevixai-backend:8000 |
| `chat.safevixai.gov.in` | `/api/v1/chat/*`, `/health` | safevixai-chatbot:8010 |
| `app.safevixai.gov.in` | `/*` | safevixai-frontend:3000 |

## External Secrets

External Secrets Operator pulls secrets from AWS SSM Parameter Store:

| Secret | SSM Path | Service |
|--------|----------|---------|
| `DATABASE_URL` | `/safevixai/prod/DATABASE_URL` | backend |
| `REDIS_URL` | `/safevixai/prod/REDIS_URL` | backend + chatbot |
| `GROQ_API_KEY` | `/safevixai/prod/GROQ_API_KEY` | chatbot |
| `ADMIN_SECRET` | `/safevixai/prod/ADMIN_SECRET` | backend |

## Monitoring

Deploy alongside `k8s/monitoring/` for Prometheus scraping + Grafana dashboards:

```bash
kubectl apply -k k8s/monitoring/
```

See `docs/runbooks/monitoring-setup.md` for alert rules and dashboard URLs.
