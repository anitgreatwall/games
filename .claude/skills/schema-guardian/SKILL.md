---
name: schema-guardian
description: Validate SQL migrations for Redoe OS. Checks naming conventions (snake_case), RLS presence, audit triggers, breaking changes, and required columns. Use when user says "validate migration", "check schema", "schema review", invokes /schema-guardian, or when reviewing SQL files in supabase/migrations/. Also runs automatically in CI via db-qa.yml.
---

# Schema Guardian — Migration Validator for Redoe OS

Static analysis of SQL migration files. No Claude API cost — pure regex/grep validation. Catches problems before they reach pgTAP or production.

## Step 1: Identify Migration Files

Determine which migration files to validate:
- If invoked with a specific file path, validate that file
- If invoked without args, find changed migrations via `git diff main -- supabase/migrations/*.sql`
- If no git context, validate all files in `supabase/migrations/`

## Step 2: Validate Filename Convention

Migration filenames must match: `YYYYMMDDHHMMSS_descriptive_name.sql`
- 14-digit timestamp prefix
- Underscore separator
- Lowercase descriptive name (a-z, 0-9, underscores only)
- `.sql` extension

Regex: `^\d{14}_[a-z][a-z0-9_]+\.sql$`

## Step 3: Check Naming Conventions

Read `references/schema-conventions.md` for the full rule set. Key checks:

Scan all SQL identifiers in the migration for violations:
- **camelCase detection:** Flag any identifier matching `[a-z][A-Z]` (e.g., `jobType` should be `job_type`)
- **Table names:** Must be snake_case, plural (warn if doesn't end in s/es/ies — heuristic only)
- **Column names:** Must be snake_case
- **Enum values:** Must be lowercase (e.g., `'Running'` should be `'running'`)
- **Function names:** Must start with `fn_` prefix

## Step 4: Check Required Columns

Every `CREATE TABLE` must include:
- `id` (SERIAL, BIGSERIAL, or UUID) as PRIMARY KEY
- `created_at TIMESTAMPTZ DEFAULT NOW()`
- `updated_at` (if table has mutable data — warn if missing, don't fail)

## Step 5: Check RLS Presence

Every `CREATE TABLE` in the migration must have a matching:
```sql
ALTER TABLE <table_name> ENABLE ROW LEVEL SECURITY;
```

If a new table lacks this, **FAIL** the check. Tables intentionally without RLS must be documented in the Security Auditor's `rls-exceptions.md`.

Also check: at least one `CREATE POLICY` for each new RLS-enabled table. RLS enabled + zero policies = deny-all (silent data loss).

## Step 6: Check Audit Triggers

Business data tables (jobs, labour, costs, POs, PRs, forms, ECOs, quality incidents) need:
```sql
CREATE TRIGGER audit_<table> AFTER INSERT OR UPDATE OR DELETE ON <table>
  FOR EACH ROW EXECUTE FUNCTION fn_audit_trigger();
```

Warn if a new table with business data lacks an audit trigger. Use heuristic: if table has `created_at` and is NOT a lookup/config table (shifts, departments, indirect_codes, break_types, scrap_reasons, downtime_reasons), it probably needs auditing.

## Step 7: Detect Breaking Changes

Flag these as **BREAKING** (requires Steve's approval):
- `DROP TABLE` or `DROP TABLE IF EXISTS`
- `DROP COLUMN`
- `ALTER COLUMN ... TYPE` (type coercion risk)
- `ALTER TYPE ... DROP VALUE` or `RENAME VALUE`
- `TRUNCATE`

Flag these as **WARNING** (review recommended):
- `ALTER TABLE ... RENAME COLUMN`
- `ALTER TYPE ... ADD VALUE` (safe but requires awareness)
- Missing `IF EXISTS` guards on DROP operations

## Step 8: Output Report

Format results as a checklist:

```
## Schema Guardian Report — [filename]

| Check | Status | Details |
|-------|--------|---------|
| Filename convention | PASS/FAIL | ... |
| Naming conventions | PASS/FAIL | N violations found |
| Required columns | PASS/FAIL | ... |
| RLS enabled | PASS/FAIL | N tables without RLS |
| Audit triggers | PASS/WARN | N tables without triggers |
| Breaking changes | PASS/WARN/FAIL | N breaking operations |

### Details
[List specific violations with line numbers]
```

## Running Locally

The `scripts/validate_migration.sh` script runs the same checks without Claude:
```bash
pnpm qa:schema                           # validate all migrations
bash .github/scripts/schema-guardian.sh   # same script, direct path
```

## Running in CI

Schema Guardian is the first job in `.github/workflows/db-qa.yml`. It runs before pgTAP tests. Failures block merge.
