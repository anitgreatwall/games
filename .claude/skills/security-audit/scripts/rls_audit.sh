#!/usr/bin/env bash
# =============================================================================
# Security Auditor — rls_audit.sh
# Checks RLS status for all public tables against Supabase
#
# Usage:
#   ./rls_audit.sh [SUPABASE_DB_URL]         # Full audit (requires DB connection)
#   ./rls_audit.sh --ci [MIGRATIONS_DIR]      # CI mode: static analysis of migrations
#
# Default DB: postgresql://postgres:postgres@127.0.0.1:54322/postgres (local)
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# ─── CI Mode: Static analysis of migration files (no DB required) ───
if [ "${1:-}" = "--ci" ]; then
  MIGRATIONS_DIR="${2:-supabase/migrations}"
  echo "============================================"
  echo "RLS Audit — CI Mode (static analysis)"
  echo "Scanning: $MIGRATIONS_DIR"
  echo "============================================"
  echo ""

  FAIL=0

  # Check: every CREATE TABLE must have a matching ENABLE ROW LEVEL SECURITY
  for f in "$MIGRATIONS_DIR"/*.sql; do
    [ -f "$f" ] || continue
    TABLES=$(grep -iP 'CREATE\s+TABLE\s+(IF\s+NOT\s+EXISTS\s+)?(public\.)?\w+' "$f" | grep -ioP '(?:public\.)?(\w+)' | tail -1 || true)
    if [ -n "$TABLES" ]; then
      for TABLE in $TABLES; do
        TABLE_CLEAN=$(echo "$TABLE" | sed 's/public\.//')
        if ! grep -iq "ALTER TABLE.*${TABLE_CLEAN}.*ENABLE ROW LEVEL SECURITY" "$f"; then
          echo -e "${RED}FAIL: $f creates table '$TABLE_CLEAN' without ENABLE ROW LEVEL SECURITY${NC}"
          ((FAIL++))
        else
          echo -e "${GREEN}OK: $f — '$TABLE_CLEAN' has RLS enabled${NC}"
        fi
      done
    fi
  done

  echo ""
  if [ $FAIL -gt 0 ]; then
    echo -e "${RED}CI RLS AUDIT: $FAIL table(s) missing RLS${NC}"
    exit 1
  else
    echo -e "${GREEN}CI RLS AUDIT: All new tables have RLS${NC}"
    exit 0
  fi
fi

# ─── Full Mode: Live database audit ───
DB_URL="${1:-postgresql://postgres:postgres@127.0.0.1:54322/postgres}"

echo "============================================"
echo "RLS Audit — Redoe OS"
echo "============================================"
echo ""

# Get all public tables with RLS status and policy count
RESULTS=$(psql "$DB_URL" -t -A -F'|' -c "
  SELECT c.relname,
         c.relrowsecurity,
         COALESCE((SELECT COUNT(*) FROM pg_policies p WHERE p.tablename = c.relname), 0) as policy_count
  FROM pg_class c
  JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE n.nspname = 'public'
  AND c.relkind = 'r'
  ORDER BY c.relname;
")

TOTAL=0
RLS_ON=0
RLS_OFF=0
NO_POLICY=0
CRITICAL=0

# Known exceptions (lookup/config tables)
EXCEPTIONS="departments shifts indirect_codes break_types scrap_reasons downtime_reasons sync_state machine_monitoring_config audit_log"

echo "| Table | RLS | Policies | Status |"
echo "|-------|-----|----------|--------|"

while IFS='|' read -r TABLE RLS_ENABLED POLICY_COUNT; do
  ((TOTAL++))

  if [ "$RLS_ENABLED" = "t" ]; then
    ((RLS_ON++))
    if [ "$POLICY_COUNT" -eq 0 ]; then
      ((NO_POLICY++))
      ((CRITICAL++))
      echo -e "| $TABLE | ON | 0 | ${RED}CRITICAL: deny-all${NC} |"
    else
      echo -e "| $TABLE | ON | $POLICY_COUNT | ${GREEN}OK${NC} |"
    fi
  else
    # Check if it's an exception
    if echo "$EXCEPTIONS" | grep -qw "$TABLE"; then
      echo -e "| $TABLE | OFF | - | ${GREEN}Exception${NC} |"
    else
      ((RLS_OFF++))
      ((CRITICAL++))
      echo -e "| $TABLE | OFF | - | ${RED}CRITICAL: no RLS${NC} |"
    fi
  fi
done <<< "$RESULTS"

echo ""
echo "============================================"
echo "Summary: $TOTAL tables | $RLS_ON with RLS | $RLS_OFF without (non-exempt) | $NO_POLICY deny-all"
echo "============================================"

if [ $CRITICAL -gt 0 ]; then
  echo -e "${RED}FAILED: $CRITICAL critical finding(s)${NC}"
  exit 1
else
  echo -e "${GREEN}PASSED: All tables properly secured${NC}"
  exit 0
fi
