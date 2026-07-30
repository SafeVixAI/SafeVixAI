#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
#
# Enterprise OSPO completion verification script for SafeVixAI.
# Checks all implemented gaps across backend, chatbot, frontend, and docs.
#
# Usage: bash scripts/verify-enterprise.sh
#   -f    Fast mode: skip mkdocs build
#   -v    Verbose: show details for each check

set -uo pipefail

FAST=false
VERBOSE=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    -f|--fast) FAST=true ; shift ;;
    -v|--verbose) VERBOSE=true ; shift ;;
    *) echo "Usage: $0 [-f] [-v]"; exit 1 ;;
  esac
done

PASS=0
FAIL=0
REPORT=()

check() {
  local name="$1" cond="$2"
  if eval "$cond" 2>/dev/null; then
    REPORT+=("  [PASS] $name")
    ((PASS++))
    return 0
  else
    REPORT+=("  [FAIL] $name")
    ((FAIL++))
    return 1
  fi
}

check_v() {
  local name="$1" cond="$2" detail="$3"
  if check "$name" "$cond"; then
    $VERBOSE && echo "    $detail" || true
  fi
}

echo "=== SafeVixAI Enterprise OSPO Verification ==="
echo "Date: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
echo ""

# ════════════════════════════════════════════════════════════
# Phase 1: Chatbot Service Endpoints
# ════════════════════════════════════════════════════════════
echo "-- Phase 1: Chatbot Service --"

check "Metrics endpoint exists" "test -f chatbot_service/core/metrics.py"
check "Metrics test file exists" "test -f chatbot_service/tests/test_metrics.py"
check "Version endpoint file" "test -f chatbot_service/api/version.py"
check "Version endpoint registered" "grep -q 'from api.version import router as version_router' chatbot_service/api/__init__.py"
check "Version tests exist" "test -f chatbot_service/tests/test_version.py"
check "Speech v1 router exists" "grep -q 'router_v1 = APIRouter' chatbot_service/api/speech.py"
check "Admin v1 router exists" "grep -q 'router_v1 = APIRouter' chatbot_service/api/admin.py"
check "API versioning tests exist" "test -f chatbot_service/tests/test_api_versioning.py"
check "Admin v1 registered" "grep -q 'admin_router_v1' chatbot_service/api/__init__.py && grep -q 'speech_router_v1' chatbot_service/api/__init__.py"

# ════════════════════════════════════════════════════════════
# Phase 2: Backend Probes
# ════════════════════════════════════════════════════════════
echo ""
echo "-- Phase 2: Backend Probes --"

check "Probes module exists" "test -f backend/api/v1/probes.py"
check "Probes registered" "grep -q 'from api.v1.probes import router as probes_router' backend/api/v1/__init__.py"
check "Probes tests exist" "test -f backend/tests/test_probes.py"
check "Startup flag wired" "grep -q 'from api.v1.probes import set_startup_complete' backend/main.py"
check "readyz endpoint" "grep -q '@router.get.*readyz' backend/api/v1/probes.py"
check "livez endpoint" "grep -q '@router.get.*livez' backend/api/v1/probes.py"
check "startupz endpoint" "grep -q '@router.get.*startupz' backend/api/v1/probes.py"

# ════════════════════════════════════════════════════════════
# Phase 3: Frontend Updates
# ════════════════════════════════════════════════════════════
echo ""
echo "-- Phase 3: Frontend Updates --"

check "PWA update hook exists" "test -f frontend/hooks/useServiceWorkerUpdate.ts"
check "PWA update hook tests exist" "test -f frontend/hooks/__tests__/useServiceWorkerUpdate.test.ts"
check "PWA update prompt component" "test -f frontend/components/updates/PwaUpdatePrompt.tsx"
check "PWA prompt tests" "test -f frontend/components/updates/__tests__/PwaUpdatePrompt.test.tsx"
check "PWA prompt integrated in layout" "grep -q 'PwaUpdatePrompt' frontend/app/layout.tsx"
check "Release notes page exists" "test -f frontend/app/release-notes/page.tsx"
check "Release notes tests exist" "test -f frontend/tests/release-notes.test.tsx"
check "ReleaseNotesViewer component" "test -f frontend/components/updates/ReleaseNotesViewer.tsx"
check "ReleaseNotesModal component" "test -f frontend/components/updates/ReleaseNotesModal.tsx"
check "Release Notes link in UpdateBanner" "grep -q 'Release Notes' frontend/components/updates/UpdateBanner.tsx"
check "CLI update script" "test -f frontend/scripts/update.mjs"
check "CLI update script entry in package.json" "grep -q '\"update\"' frontend/package.json"

# ════════════════════════════════════════════════════════════
# Phase 4: Documentation
# ════════════════════════════════════════════════════════════
echo ""
echo "-- Phase 4: Documentation --"

check "Tutorials index exists" "test -f docs/tutorials/index.md"
check "SOS tutorial exists" "test -f docs/tutorials/sos-setup.md"
check "Challan tutorial exists" "test -f docs/tutorials/challan-integration.md"
check "Chatbot tutorial exists" "test -f docs/tutorials/chatbot-customization.md"
check "SYSTEM_DESIGN.md exists" "test -f docs/SYSTEM_DESIGN.md"
check "DEVELOPER_GUIDE.md exists" "test -f docs/DEVELOPER_GUIDE.md"
check "mkdocs.yml Tutorials nav sub-menu" "grep -q 'Tutorials:' mkdocs.yml && grep -q 'SOS Setup:' mkdocs.yml"
check "mkdocs.yml CLI Reference nav entry" "grep -q 'CLI Reference:' mkdocs.yml"
check "mkdocs.yml System Design nav entry" "grep -q 'System Design: SYSTEM_DESIGN.md' mkdocs.yml"
check "mkdocs.yml Developer Guide nav entry" "grep -q 'Developer Guide: DEVELOPER_GUIDE.md' mkdocs.yml"
check "mkdocs.yml mike version selector" "grep -q 'provider: mike' mkdocs.yml"

if ! $FAST; then
  echo ""
  echo "-- mkdocs build --"
  if python -m mkdocs build --strict 2>/dev/null; then
    echo "  [PASS] mkdocs build"
    ((PASS++))
  else
    echo "  [FAIL] mkdocs build"
    ((FAIL++))
  fi
fi

# ════════════════════════════════════════════════════════════
# Phase 5: Templates & Scaffolding
# ════════════════════════════════════════════════════════════
echo ""
echo "-- Phase 5: Templates --"

check "cookiecutter config exists" "test -f templates/project-scaffold/cookiecutter.json"
check "README template exists" "test -f templates/project-scaffold/{{cookiecutter.project_name}}/README.md"
check "Makefile template exists" "test -f templates/project-scaffold/{{cookiecutter.project_name}}/Makefile"
check "docker-compose template exists" "test -f templates/project-scaffold/{{cookiecutter.project_name}}/docker-compose.yml"
check "backend init template" "test -f templates/project-scaffold/{{cookiecutter.project_name}}/backend/__init__.py"
check "frontend package template" "test -f templates/project-scaffold/{{cookiecutter.project_name}}/frontend/package.json"
check "tests init template" "test -f templates/project-scaffold/{{cookiecutter.project_name}}/tests/__init__.py"
check "docs index template" "test -f templates/project-scaffold/{{cookiecutter.project_name}}/docs/index.md"

# ════════════════════════════════════════════════════════════
# Summary
# ════════════════════════════════════════════════════════════
echo ""
echo "-- Results --"
for r in "${REPORT[@]}"; do echo "$r"; done
echo ""
if [[ $FAIL -eq 0 ]]; then
  echo "All $PASS checks passed!"
  exit 0
else
  echo "$PASS passed, $FAIL failed"
  exit 1
fi
