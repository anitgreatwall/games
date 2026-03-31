#!/usr/bin/env bash
# =============================================================================
# Schema Guardian — validate_migration.sh
# Static analysis for Redoe OS SQL migrations
# Usage: ./validate_migration.sh [file1.sql] [file2.sql] ...
#        If no args, validates all files in supabase/migrations/
# Exit codes: 0 = pass, 1 = fail (blocking), 2 = warnings only
# =============================================================================

set -euo pipefail

ERRORS=0
WARNINGS=0

# Determine files to check
if [ $# -gt 0 ]; then
  FILES="$@"
else
  FILES=$(find supabase/migrations -name '*.sql' 2>/dev/null || echo "")
  if [ -z "$FILES" ]; then
    echo "No migration files found in supabase/migrations/"
    exit 0
  fi
fi

# Color output (if terminal supports it)
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
NC='\033[0m'

fail() { echo -e "${RED}FAIL${NC}: $1"; ((ERRORS++)); }
warn() { echo -e "${YELLOW}WARN${NC}: $1"; ((WARNINGS++)); }
pass() { echo -e "${GREEN}PASS${NC}: $1"; }

echo "============================================"
echo "Schema Guardian — Redoe OS Migration Validator"
echo "============================================"
echo ""

for FILE in $FILES; do
  BASENAME=$(basename "$FILE")
  echo "--- Checking: $BASENAME ---"

  # -----------------------------------------------
  # CHECK 1: Filename convention
  # YYYYMMDDHHMMSS_descriptive_name.sql
  # -----------------------------------------------
  if echo "$BASENAME" | grep -qP '^\d{14}_[a-z][a-z0-9_]+\.sql$'; then
    pass "Filename convention"
  else
    fail "Filename must match YYYYMMDDHHMMSS_descriptive_name.sql (lowercase). Got: $BASENAME"
  fi

  # -----------------------------------------------
  # CHECK 2: camelCase detection
  # Flag identifiers with lowercase-then-uppercase pattern
  # Exclude comments (lines starting with --)
  # -----------------------------------------------
  CAMEL=$(grep -nP '^[^-]*[a-z][A-Z]' "$FILE" | grep -viP '(--|/\*|\*/|https?://|camelCase|JSON|JSONB|UTF|OAuth|GitHub|TypeScript|JavaScript|PostgreSQL|NextJS|README)' || true)
  if [ -n "$CAMEL" ]; then
    fail "camelCase detected (must use snake_case):"
    echo "$CAMEL" | head -5
  else
    pass "Naming conventions (no camelCase)"
  fi

  # -----------------------------------------------
  # CHECK 3: Uppercase enum values
  # -----------------------------------------------
  UPPER_ENUM=$(grep -nP "CREATE TYPE.*ENUM" "$FILE" | grep -P "'[A-Z]" || true)
  if [ -n "$UPPER_ENUM" ]; then
    warn "Enum values should be lowercase:"
    echo "$UPPER_ENUM" | head -3
  fi

  # -----------------------------------------------
  # CHECK 4: Required columns on CREATE TABLE
  # -----------------------------------------------
  TABLE_NAMES=$(grep -oP 'CREATE TABLE (?:IF NOT EXISTS )?\K[a-z_]+' "$FILE" || true)
  for TABLE in $TABLE_NAMES; do
    # Extract the CREATE TABLE block (rough: from CREATE TABLE to next );)
    # Check for created_at
    if ! grep -qP "created_at\s+TIMESTAMPTZ" "$FILE"; then
      warn "$TABLE: Missing 'created_at TIMESTAMPTZ' column"
    fi
  done

  # -----------------------------------------------
  # CHECK 5: RLS enabled on new tables
  # -----------------------------------------------
  for TABLE in $TABLE_NAMES; do
    if ! grep -qiP "ALTER TABLE\s+$TABLE\s+ENABLE\s+ROW\s+LEVEL\s+SECURITY" "$FILE"; then
      fail "$TABLE: Missing ALTER TABLE $TABLE ENABLE ROW LEVEL SECURITY"
    else
      # Check for at least one policy
      if ! grep -qiP "CREATE POLICY\s+\S+\s+ON\s+$TABLE" "$FILE"; then
        warn "$TABLE: RLS enabled but no policies defined (deny-all). Add a policy or document exception."
      else
        pass "$TABLE: RLS enabled with policy"
      fi
    fi
  done

  # -----------------------------------------------
  # CHECK 6: Breaking changes
  # -----------------------------------------------
  if grep -qiP '\bDROP\s+TABLE\b' "$FILE"; then
    fail "BREAKING: DROP TABLE detected. Requires Steve's approval."
  fi
  if grep -qiP '\bDROP\s+COLUMN\b' "$FILE"; then
    fail "BREAKING: DROP COLUMN detected. Requires Steve's approval."
  fi
  if grep -qiP 'ALTER\s+COLUMN\s+\S+\s+TYPE\b' "$FILE"; then
    fail "BREAKING: ALTER COLUMN TYPE detected. Type coercion risk."
  fi
  if grep -qiP '\bTRUNCATE\b' "$FILE"; then
    fail "BREAKING: TRUNCATE detected. Data loss risk."
  fi
  if grep -qiP 'ALTER\s+TYPE\s+\S+\s+DROP\s+VALUE' "$FILE"; then
    fail "BREAKING: DROP enum value detected."
  fi
  if grep -qiP 'ALTER\s+TABLE\s+\S+\s+RENAME\s+COLUMN' "$FILE"; then
    warn "Column rename detected. Verify all application queries are updated."
  fi

  # -----------------------------------------------
  # CHECK 7: SECURITY DEFINER functions
  # -----------------------------------------------
  if grep -qiP 'SECURITY\s+DEFINER' "$FILE"; then
    warn "SECURITY DEFINER function detected. Only fn_audit_trigger should use DEFINER. Verify this is intentional."
  fi

  # -----------------------------------------------
  # CHECK 8: TIMESTAMP vs TIMESTAMPTZ
  # -----------------------------------------------
  if grep -qP '\bTIMESTAMP\b' "$FILE" && ! grep -qP '\bTIMESTAMPTZ\b' "$FILE"; then
    warn "TIMESTAMP used without TZ. Redoe OS standard is TIMESTAMPTZ."
  fi

  echo ""
done

# -----------------------------------------------
# SUMMARY
# -----------------------------------------------
echo "============================================"
echo "SUMMARY: $ERRORS error(s), $WARNINGS warning(s)"
echo "============================================"

if [ $ERRORS -gt 0 ]; then
  echo -e "${RED}FAILED${NC} — fix errors before merging"
  exit 1
elif [ $WARNINGS -gt 0 ]; then
  echo -e "${YELLOW}PASSED with warnings${NC}"
  exit 0
else
  echo -e "${GREEN}ALL CHECKS PASSED${NC}"
  exit 0
fi
