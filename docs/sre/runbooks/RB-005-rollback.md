# RB-005: Deployment Rollback

**Severity:** P1  
**Last Updated:** 2026-06-16  
**Owner:** SRE  

## Symptoms

- Deployment stuck in progress
- New pods crash-looping
- Health checks failing after rollout
- CloudWatch alarms triggering after deploy

## Resolution

### Step 1: Rollback Kubernetes Deployment
```bash
# View rollout history
kubectl rollout history deployment/safevixai-backend -n safevixai

# Rollback to previous revision
kubectl rollout undo deployment/safevixai-backend -n safevixai

# Or rollback to a specific revision
kubectl rollout undo deployment/safevixai-backend -n safevixai --to-revision=3

# Verify rollback
kubectl rollout status deployment/safevixai-backend -n safevixai --timeout=5m
```

### Step 2: Rollback ECS (AWS Fargate)
```bash
# Update service to use previous task definition
aws ecs update-service \
  --cluster safevixai-cluster \
  --service safevixai-backend \
  --task-definition safevixai-backend:3  # Previous revision number

# Wait for steady state
aws ecs wait services-stable \
  --cluster safevixai-cluster \
  --services safevixai-backend
```

### Step 3: Rollback Docker Image (ECR)
```bash
# Tag previous image as latest
docker pull $ECR_REGISTRY/safevixai/backend:previous-tag
docker tag $ECR_REGISTRY/safevixai/backend:previous-tag $ECR_REGISTRY/safevixai/backend:latest
docker push $ECR_REGISTRY/safevixai/backend:latest

# Trigger redeploy
kubectl rollout restart deployment/safevixai-backend -n safevixai
```

### ECS Deployment Circuit Breaker
ECS is configured with `deployment_circuit_breaker { enable = true; rollback = true }`.  
If the new task definition fails health checks, it automatically rolls back.

## Prevention
- Deployment circuit breaker (auto-rollback on failure)
- Blue-green deployment for zero-downtime
- Canary analysis in CI
- Load test before production deploy