# SafeVixAI — Terraform (AWS)

Infrastructure-as-Code for deploying SafeVixAI on AWS ECS Fargate.

## Architecture

```
Internet → Route53 → CloudFront/WAF → ALB → ECS Fargate (backend + chatbot + frontend)
                                              → RDS (PostgreSQL + PostGIS)
                                              → ElastiCache (Redis)
                                              → S3 (media assets)
```

## Modules

| File | Resource | Purpose |
|------|----------|---------|
| `main.tf` | VPC, subnets, NAT, flow logs | Network foundation |
| `ecs.tf` | ECS cluster + Fargate services | backend (:8000), chatbot (:8010), frontend (:3000) |
| `rds.tf` | RDS PostgreSQL 16 + PostGIS | Database with automated backups |
| `elasticache.tf` | Redis 7 (cluster mode) | Caching + session store |
| `alb.tf` | Application Load Balancer | Path-based routing to services |
| `api_gateway.tf` | API Gateway | REST throttling + WAF integration |
| `waf.tf` | WAF ACL | Rate limiting, SQLi/XSS blocking |
| `autoscaling.tf` | Application Auto Scaling | CPU/memory-based scaling policies |
| `route53.tf` | DNS records | api.safevixai.gov.in etc. |
| `iam.tf` | IAM roles + policies | Least-privilege task execution |
| `ecr.tf` | ECR repositories | Container image storage |
| `s3.tf` | Buckets | Uploads, logs, backups |
| `secrets.tf` | Secrets Manager | API keys, DB credentials |
| `monitoring.tf` | CloudWatch dashboards + alarms | Observability |
| `backend.tf` | Terraform state (S3 + DynamoDB) | Remote state locking |
| `variables.tf` | Input variables | Environment configuration |
| `outputs.tf` | Output values | Endpoints, ARNs |

## Usage

```bash
# Init
terraform init -backend-config=environments/prod/backend.hcl

# Plan
terraform plan -var-file=environments/prod/terraform.tfvars

# Apply
terraform apply -var-file=environments/prod/terraform.tfvars

# Destroy (DR/test only)
terraform destroy -var-file=environments/prod/terraform.tfvars
```

## Environments

| Env | TFVars | Notes |
|-----|--------|-------|
| `dev` | `environments/dev/terraform.tfvars` | Min replicas, t3.small |
| `staging` | `environments/staging/terraform.tfvars` | t3.medium, pre-prod |
| `prod` | `environments/prod/terraform.tfvars` | t3.large, AZ HA, auto-scaling |
