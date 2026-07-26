.PHONY: help setup test lint build docker docker-up docker-down clean deploy \
        e2e terraform-fmt terraform-validate terraform-plan terraform-apply \
        k8s-apply k8s-delete k8s-status k8s-logs k6-smoke k6-load k6-sustained k6-spike \
        ecr-login ecr-build ecr-push security-scan \
        update-check update-download update-install update-rollback update-history update-sync \
        backend-migrate backend-migrate-head

SHELL := /bin/bash
# NOTE: Windows contributors should use `make` via WSL, Git Bash, or Docker.
# The `find`, `rm -rf` and `cp` commands work across all three.
TF_DIR := terraform
K8S_DIR := k8s
K6_DIR := load-testing/k6

help:
	@echo "╔══════════════════════════════════════════════════════╗"
	@echo "║              SafeVixAI Development CLI              ║"
	@echo "╠══════════════════════════════════════════════════════╣"
	@echo "║  Development                                         ║"
	@echo "║    make setup          Install all deps + copy .env  ║"
	@echo "║    make test           Run all tests                 ║"
	@echo "║    make lint           Lint all code                 ║"
	@echo "║    make typecheck     TypeScript type-check         ║"
	@echo "║    make build          Build frontend                ║"
	@echo "║                                                     ║"
	@echo "║  Docker                                              ║"
	@echo "║    make docker         Build Docker images           ║"
	@echo "║    make docker-up      Start Docker Compose          ║"
	@echo "║    make docker-down    Stop Docker Compose           ║"
	@echo "║    make ecr-login      Login to AWS ECR              ║"
	@echo "║    make ecr-push       Build + push to ECR           ║"
	@echo "║                                                     ║"
	@echo "║  Infrastructure (Terraform)                          ║"
	@echo "║    make tf-fmt        Format Terraform               ║"
	@echo "║    make tf-validate   Validate Terraform             ║"
	@echo "║    make tf-plan       Terraform plan                 ║"
	@echo "║    make tf-apply      Terraform apply                ║"
	@echo "║                                                     ║"
	@echo "║  Kubernetes                                          ║"
	@echo "║    make k8s-apply     Deploy to K8s                  ║"
	@echo "║    make k8s-status    K8s pod status                 ║"
	@echo "║    make k8s-logs     Tail service logs               ║"
	@echo "║    make k8s-delete    Tear down K8s                  ║"
	@echo "║                                                     ║"
	@echo "║  Load Testing (k6)                                   ║"
	@echo "║    make k6-smoke      Quick smoke test               ║"
	@echo "║    make k6-load       Multi-scenario load test       ║"
	@echo "║    make k6-sustained  15-min sustained load          ║"
	@echo "║    make k6-spike      Emergency endpoint spike       ║"
	@echo "║                                                     ║"
	@echo "║  Quality                                             ║"
	@echo "║    make e2e           Run Playwright E2E tests       ║"
	@echo "║    make security-scan Run Gitleaks + Trivy           ║"
	@echo "║    make clean         Clean artifacts                ║"
	@echo "║                                                     ║"
	@echo "║  Deployment                                          ║"
	@echo "║    make deploy        Deploy to production           ║"
	@echo "╚══════════════════════════════════════════════════════╝"

# === Development ===

setup:
	cd backend && python -m pip install -r requirements.txt && cp -n .env.example .env 2>/dev/null || true
	cd chatbot_service && python -m pip install -r requirements.txt && cp -n .env.example .env 2>/dev/null || true
	cd frontend && npm ci && cp -n .env.local.example .env.local 2>/dev/null || true
	@echo "✓ Dependencies installed. Edit .env files with your keys."

test:
	cd backend && PYTHONPATH=. pytest tests/ -q --tb=short
	cd chatbot_service && PYTHONPATH=. pytest tests/ -q --tb=short
	cd frontend && npm test -- --watchAll=false --no-coverage

test-backend:
	cd backend && PYTHONPATH=. pytest tests/ -v --tb=short -q

test-chatbot:
	cd chatbot_service && PYTHONPATH=. pytest tests/ -v --tb=short -q

test-frontend:
	cd frontend && npm test -- --watchAll=false --no-coverage

lint:
	cd backend && ruff check .
	cd chatbot_service && ruff check .
	cd frontend && npm run lint

typecheck:
	cd frontend && npx tsc --noEmit

build:
	cd frontend && npm run build

# === Docker ===

docker:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

ecr-login:
	aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin $(AWS_ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com

ecr-build-push-backend:
	docker build -t safevixai/backend:latest backend/
	docker tag safevixai/backend:latest $(AWS_ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com/safevixai/backend:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com/safevixai/backend:latest

ecr-build-push-chatbot:
	docker build -t safevixai/chatbot:latest chatbot_service/
	docker tag safevixai/chatbot:latest $(AWS_ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com/safevixai/chatbot:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com/safevixai/chatbot:latest

ecr-build-push-frontend:
	docker build -f frontend/Dockerfile.frontend -t safevixai/frontend:latest frontend/
	docker tag safevixai/frontend:latest $(AWS_ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com/safevixai/frontend:latest
	docker push $(AWS_ACCOUNT_ID).dkr.ecr.ap-south-1.amazonaws.com/safevixai/frontend:latest

ecr-build-push-all: ecr-build-push-backend ecr-build-push-chatbot ecr-build-push-frontend

# === Terraform ===

tf-fmt:
	cd $(TF_DIR) && terraform fmt -recursive

tf-validate:
	cd $(TF_DIR) && terraform init -backend=false && terraform validate

tf-plan:
	cd $(TF_DIR) && terraform plan -no-color -out=tfplan

tf-apply:
	cd $(TF_DIR) && terraform apply -no-color tfplan

tf-destroy:
	cd $(TF_DIR) && terraform destroy

# === Kubernetes ===

k8s-apply:
	kubectl apply -k $(K8S_DIR)

k8s-delete:
	kubectl delete -k $(K8S_DIR)

k8s-status:
	kubectl get pods,svc,ingress,hpa,pdb,networkpolicy -n safevixai

k8s-logs:
	kubectl logs -n safevixai -l app.kubernetes.io/part-of=safevixai --tail=100 -f

k8s-rollout-backend:
	kubectl rollout restart deployment/safevixai-backend -n safevixai
	kubectl rollout status deployment/safevixai-backend -n safevixai --timeout=5m

k8s-rollout-chatbot:
	kubectl rollout restart deployment/safevixai-chatbot -n safevixai
	kubectl rollout status deployment/safevixai-chatbot -n safevixai --timeout=10m

k8s-rollout-frontend:
	kubectl rollout restart deployment/safevixai-frontend -n safevixai
	kubectl rollout status deployment/safevixai-frontend -n safevixai --timeout=5m

# === Load Testing ===

k6-smoke:
	k6 run $(K6_DIR)/smoke.test.js

k6-load:
	k6 run $(K6_DIR)/main.test.js

k6-sustained:
	k6 run $(K6_DIR)/sustained-load.test.js

k6-spike:
	k6 run $(K6_DIR)/emergency-spike.test.js

# === Quality ===

e2e:
	cd frontend && npx playwright test e2e/ --grep-invert="Visual Regression|visual"

security-scan:
	gitleaks detect --source . --verbose
	trivy fs --severity HIGH,CRITICAL --no-progress .

# === Clean ===

clean:
	cd backend && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd chatbot_service && find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	cd frontend && rm -rf .next coverage test-results playwright-report
	cd frontend && rm -f lint_output.txt ts-errors.txt log.txt ls_recursive.txt eslint.json
	rm -rf .pytest_cache .ruff_cache htmlcov
	@echo "✓ Cleaned build artifacts"

# === Updates ===

update-check:
	@echo "Checking for updates..."
	cd backend && PYTHONPATH=. python ../scripts/safevixai_update.py check

update-download:
	cd backend && PYTHONPATH=. python ../scripts/safevixai_update.py download

update-install:
	cd backend && PYTHONPATH=. python ../scripts/safevixai_update.py install

update-rollback:
	cd backend && PYTHONPATH=. python ../scripts/safevixai_update.py rollback

update-history:
	cd backend && PYTHONPATH=. python ../scripts/safevixai_update.py history

update-sync:
	cd backend && PYTHONPATH=. python ../scripts/safevixai_update.py sync

# === Migrations ===

backend-migrate:
	cd backend && alembic upgrade head

backend-migrate-head:
	cd backend && alembic heads

backend-migrate-downgrade:
	cd backend && alembic downgrade -1

backend-migration-create:
	cd backend && read -p "Migration name: " name; alembic revision --autogenerate -m "$$name"

# === Deploy ===

deploy:
	@echo "=== Deploying SafeVixAI ==="
	cd $(TF_DIR) && terraform apply -auto-approve
	kubectl apply -k $(K8S_DIR)
	@echo "=== Deployment complete ==="
