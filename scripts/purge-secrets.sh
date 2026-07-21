#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team
# ============================================================================
# purge-secrets.sh — Purge .env files and secrets from Git history
#
# Uses git-filter-repo (preferred) or git-filter-branch to permanently remove
# sensitive files and credentials from the entire commit history.
#
# Usage:
#   ./scripts/purge-secrets.sh            # interactive — prompts before exec
#   ./scripts/purge-secrets.sh --dry-run  # show what would be removed only
#   ./scripts/purge-secrets.sh --force    # skip confirmation (CI use)
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

DRY_RUN=false
FORCE=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --force)   FORCE=true   ;;
  esac
done

check_prereqs() {
  if command -v git-filter-repo &>/dev/null; then
    FILTER_TOOL="git-filter-repo"
  elif command -v git &>/dev/null; then
    FILTER_TOOL="git-filter-branch"
    echo -e "${YELLOW}⚠  git-filter-repo not found; falling back to git-filter-branch.${NC}"
  else
    echo -e "${RED}✖  git is not installed. Aborting.${NC}"
    exit 1
  fi
  cd "$REPO_ROOT"
  if ! git rev-parse --git-dir &>/dev/null; then
    echo -e "${RED}✖  Not inside a Git repository.${NC}"
    exit 1
  fi
}

SECRET_FILES=(
  '.env' '.env.*' '**/.env' '**/.env.*'
  '*.pem' '*.key' 'id_rsa*' 'id_ecdsa*'
  'secrets.yml' 'secrets.yaml'
)

confirm_or_exit() {
  cd "$REPO_ROOT"
  echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
  echo -e "${CYAN}  SafeVixAI — Git History Secret Purge${NC}"
  echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
  echo ""
  echo -e "${YELLOW}Files / paths that will be removed from history:${NC}"
  for p in "${SECRET_FILES[@]}"; do echo "  \u2022 $p"; done
  echo ""
  echo -e "${RED}⚠  THIS WILL REWRITE GIT HISTORY. All team members will need" >&2
  echo -e "   to clone fresh after you force-push.${NC}" >&2
  echo ""
  if [ "$DRY_RUN" = true ]; then
    echo -e "${YELLOW}◆  DRY RUN — no changes will be made.${NC}"
    git log --all --full-history --diff-filter=A --name-only --pretty=format: -- '.env*' 2>/dev/null | sort -u | sed 's/^/  /'
    return 0
  fi
  if [ "$FORCE" = true ]; then return 0; fi
  read -rp "Are you SURE you want to rewrite history? [y/N] " answer
  case "$answer" in
    [yY]|[yY][eE][sS]) echo "" ;;
    *) echo -e "${YELLOW}Aborted.${NC}"; exit 0 ;;
  esac
}

execute_purge() {
  cd "$REPO_ROOT"
  if [ "$DRY_RUN" = true ]; then echo -e "${GREEN}◆  Dry-run complete. No changes.${NC}"; exit 0; fi
  BACKUP_DIR="/tmp/purge-secrets-backup-$(date +%s)"
  git clone --bare "$REPO_ROOT" "$BACKUP_DIR" 2>/dev/null || true
  echo -e "${GREEN}   Backup at: $BACKUP_DIR${NC}"
  echo -e "${GREEN}◆  Starting purge ...${NC}"
  if [ "$FILTER_TOOL" = "git-filter-repo" ]; then
    git filter-repo --invert-paths \
      --path '.env' --path '.env.local' --path '.env.production' \
      --path '.env.development' --path '.env.staging' \
      --path-glob '*.pem' --path-glob '*.key' \
      --path 'secrets.yml' --path 'secrets.yaml' \
      ${FORCE:+--force}
  else
    git filter-branch --force --index-filter \
      "git rm --cached --ignore-unmatch \
        .env .env.local .env.production .env.development .env.staging \
        *.pem *.key secrets.yml secrets.yaml 2>/dev/null || true" \
      --prune-empty --tag-name-filter cat -- --all
  fi
}

post_purge_instructions() {
  echo ""
  echo -e "${GREEN}✔  Purge complete.${NC}"
  echo ""
  echo "Next steps:"
  echo "  1. Verify history:   git log --all --diff-filter=A -- '*.env'"
  echo "  2. Force-push:       git push origin --force --all"
  echo "  3. Force-push tags:  git push origin --force --tags"
  echo "  4. Instruct team to clone fresh."
  echo "  5. Delete backup:    rm -rf $BACKUP_DIR"
}

check_prereqs
confirm_or_exit
execute_purge
post_purge_instructions
