#!/usr/bin/env bash
# =============================================================================
# Security Auditor — secrets_scan.sh
# Scans Redoe OS codebase for exposed secrets and credentials
# Usage: ./secrets_scan.sh [directory]
# Exit codes: 0 = clean, 1 = secrets found
# =============================================================================

set -euo pipefail

DIR="${1:-.}"
FOUND=0

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "============================================"
echo "Secrets Scan — Redoe OS"
echo "Scanning: $DIR"
echo "============================================"
echo ""

# Exclude patterns
EXCLUDE="--exclude-dir=node_modules --exclude-dir=.git --exclude-dir=.next --exclude-dir=dist --exclude-dir=.turbo"

# File types to scan (includes HTML — Redoe OS frontend is static HTML + vanilla JS)
INCLUDES="--include=*.ts --include=*.tsx --include=*.js --include=*.html --include=*.sql --include=*.env --include=*.yml --include=*.json"

# 1. JWT tokens (eyJ prefix)
echo "--- Checking: JWT tokens ---"
JWTS=$(grep -rn $EXCLUDE 'eyJ[A-Za-z0-9_-]\{20,\}' "$DIR" $INCLUDES 2>/dev/null || true)
if [ -n "$JWTS" ]; then
  echo -e "${RED}FOUND: JWT tokens in source code${NC}"
  echo "$JWTS" | head -5
  ((FOUND++))
else
  echo -e "${GREEN}CLEAN${NC}"
fi

# 2. Supabase keys
echo ""
echo "--- Checking: Supabase keys ---"
SB_KEYS=$(grep -rn $EXCLUDE 'sb_[a-zA-Z0-9]\{20,\}' "$DIR" $INCLUDES 2>/dev/null || true)
if [ -n "$SB_KEYS" ]; then
  echo -e "${RED}FOUND: Supabase keys in source${NC}"
  echo "$SB_KEYS" | head -5
  ((FOUND++))
else
  echo -e "${GREEN}CLEAN${NC}"
fi

# 3. service_role in frontend
echo ""
echo "--- Checking: service_role in frontend ---"
SR=$(grep -rn $EXCLUDE 'service_role' "$DIR/apps/" 2>/dev/null | grep -v node_modules | grep -v 'REDOE-supabase-svr' || true)
if [ -n "$SR" ]; then
  echo -e "${RED}CRITICAL: service_role key referenced in frontend code${NC}"
  echo "$SR" | head -5
  ((FOUND++))
else
  echo -e "${GREEN}CLEAN${NC}"
fi

# 4. Connection strings
echo ""
echo "--- Checking: Connection strings ---"
CONN=$(grep -rn $EXCLUDE 'postgresql://[^$]' "$DIR" $INCLUDES 2>/dev/null || true)
if [ -n "$CONN" ]; then
  echo -e "${RED}FOUND: PostgreSQL connection strings${NC}"
  echo "$CONN" | head -5
  ((FOUND++))
else
  echo -e "${GREEN}CLEAN${NC}"
fi

# 5. Known API keys (env var names vs hardcoded values)
echo ""
echo "--- Checking: Known API key patterns ---"
APIS=$(grep -rn $EXCLUDE 'ANTHROPIC_API_KEY\|OPENAI_API_KEY\|sk-[a-zA-Z0-9]\{20,\}' "$DIR" $INCLUDES 2>/dev/null || true)
if [ -n "$APIS" ]; then
  echo -e "${YELLOW}WARNING: API key references found (verify they are env var names, not values)${NC}"
  echo "$APIS" | head -5
  ((FOUND++))
else
  echo -e "${GREEN}CLEAN${NC}"
fi

# 5b. Hardcoded secrets in client-side code (generic detection)
echo ""
echo "--- Checking: Hardcoded secrets in frontend ---"
# Matches: API_KEY = 'value', apiKey: 'value', api-key: 'value' (with actual string values, not env refs)
HARDCODED=$(grep -rn $EXCLUDE -i "api.key.*=.*'[a-zA-Z0-9_-]\{10,\}'" "$DIR" --include='*.html' --include='*.js' --include='*.ts' --include='*.tsx' 2>/dev/null | grep -v 'process\.env' | grep -v 'node_modules' | grep -v '\.example' || true)
if [ -n "$HARDCODED" ]; then
  echo -e "${RED}CRITICAL: Hardcoded API key/secret values in client code${NC}"
  echo "$HARDCODED" | head -10
  ((FOUND++))
else
  echo -e "${GREEN}CLEAN${NC}"
fi

# 5c. Generic password/token/secret assignments with literal values
echo ""
echo "--- Checking: Hardcoded passwords/tokens ---"
PASSWORDS=$(grep -rn $EXCLUDE -iE "(password|token|secret)\s*[:=]\s*['\"][^'\"]{8,}['\"]" "$DIR" --include='*.html' --include='*.js' --include='*.ts' --include='*.tsx' 2>/dev/null | grep -v 'process\.env' | grep -v 'node_modules' | grep -v '\.example' | grep -v 'placeholder' | grep -v 'type=' || true)
if [ -n "$PASSWORDS" ]; then
  echo -e "${RED}CRITICAL: Hardcoded password/token/secret values${NC}"
  echo "$PASSWORDS" | head -10
  ((FOUND++))
else
  echo -e "${GREEN}CLEAN${NC}"
fi

# 6. .env files committed
echo ""
echo "--- Checking: .env files ---"
ENVS=$(find "$DIR" -name '.env' -o -name '.env.local' -o -name '.env.production' 2>/dev/null | grep -v node_modules || true)
if [ -n "$ENVS" ]; then
  echo -e "${RED}FOUND: .env files in repository${NC}"
  echo "$ENVS"
  ((FOUND++))
else
  echo -e "${GREEN}CLEAN${NC}"
fi

# 7. Check .gitignore coverage
echo ""
echo "--- Checking: .gitignore ---"
if [ -f "$DIR/.gitignore" ]; then
  for PATTERN in ".env" ".env.local" ".env.production"; do
    if grep -q "$PATTERN" "$DIR/.gitignore"; then
      echo -e "${GREEN}$PATTERN in .gitignore${NC}"
    else
      echo -e "${YELLOW}WARNING: $PATTERN not in .gitignore${NC}"
      ((FOUND++))
    fi
  done
else
  echo -e "${YELLOW}WARNING: No .gitignore file found${NC}"
fi

# Summary
echo ""
echo "============================================"
if [ $FOUND -gt 0 ]; then
  echo -e "${RED}SECRETS SCAN: $FOUND issue(s) found${NC}"
  exit 1
else
  echo -e "${GREEN}SECRETS SCAN: CLEAN${NC}"
  exit 0
fi
