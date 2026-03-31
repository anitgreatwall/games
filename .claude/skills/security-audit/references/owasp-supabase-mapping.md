# OWASP Top 10 — Supabase-Specific Checks for Redoe OS

## A01: Broken Access Control

**What to check:**
- Every RLS policy references `auth.uid()` or `auth.jwt()` — no policy should allow access without authentication
- `USING (TRUE)` policies are intentional (only machine_events, machine_alerts, labour_entries SELECT)
- No table with sensitive data lacks RLS
- `service_role` key is NEVER used in frontend code (bypasses all RLS)
- Edge Functions check `authorization` header before processing

**How to check:**
```sql
-- Find policies with USING (TRUE) — verify each is intentional
SELECT tablename, policyname, cmd, qual
FROM pg_policies WHERE qual = 'true';
```

```bash
# service_role in frontend
grep -rn 'service_role' apps/web/ packages/
```

## A02: Cryptographic Failures

**What to check:**
- No API keys, tokens, or passwords in committed code
- No Supabase project URL with service_role key in source
- `.env` files in `.gitignore`
- Supabase auth configured for email+password (not magic link without rate limiting)

**How to check:**
```bash
# JWT-like patterns
grep -rn 'eyJ[A-Za-z0-9_-]\{20,\}' --include='*.ts' --include='*.sql'
# Password patterns
grep -rn 'password.*=.*["\x27]' --include='*.ts' --include='*.env'
```

## A03: Injection

**What to check:**
- No template literal SQL: `` `SELECT * FROM ${table}` ``
- All Supabase queries use the client SDK (parameterized by default)
- Edge Functions use `supabase.from('table').select()` not raw SQL
- If raw SQL is needed, use `supabase.rpc('function_name', params)`

**How to check:**
```bash
# Template literals with SQL keywords
grep -rn '`.*SELECT.*\$\{' apps/web/ supabase/functions/
grep -rn '`.*INSERT.*\$\{' apps/web/ supabase/functions/
grep -rn '`.*UPDATE.*\$\{' apps/web/ supabase/functions/
```

## A04: Insecure Design

**What to check:**
- Functions are `SECURITY INVOKER` by default (runs as calling user, RLS applies)
- Only `fn_audit_trigger` should be `SECURITY DEFINER` (needs to write to audit_log regardless of user)
- No function bypasses RLS unintentionally
- Approval workflows enforce state transitions (can't skip SUBMITTED and go straight to APPROVED)

**How to check:**
```sql
SELECT proname, prosecdef
FROM pg_proc p JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public' AND p.prosecdef = true;
-- Should only return fn_audit_trigger
```

## A05: Security Misconfiguration

**What to check:**
- Supabase anon key used in frontend (correct — limited permissions)
- service_role key used only in server-side code / CI (never frontend)
- CORS not set to wildcard `*` in production
- Auth rate limiting enabled
- Email confirmation required for new accounts

**How to check:**
```bash
# Check Supabase config
cat supabase/config.toml | grep -A5 'auth'
# Check CORS
grep -rn 'Access-Control-Allow-Origin' supabase/functions/
```

## A06: Vulnerable and Outdated Components

**How to check:**
```bash
pnpm audit
# Check for critical/high severity
pnpm audit --audit-level=high
```

Flag any `critical` or `high` severity finding as CRITICAL in the report.

## A07: Identification and Authentication Failures

**What to check:**
- Password minimum length >= 8 characters
- Session timeout configured (not infinite)
- JWT expiry reasonable (default 3600s = 1 hour)
- No hardcoded credentials in test files that match production patterns
- Rate limiting on auth endpoints

**How to check:**
```bash
cat supabase/config.toml | grep -A20 '\[auth\]'
```

## A08: Software and Data Integrity Failures

**What to check:**
- Foreign key constraints on all relationship columns
- `ON DELETE` behavior specified (no implicit RESTRICT without intent)
- Enum types used for constrained values (not free text)
- `CHECK` constraints on percentage fields (0-100), amounts (>= 0)

**How to check:**
```sql
-- Find columns that reference other tables but lack FK
-- (manual review — look for columns ending in _id without FK constraint)
SELECT c.table_name, c.column_name
FROM information_schema.columns c
WHERE c.column_name LIKE '%_id'
AND c.table_schema = 'public'
AND NOT EXISTS (
  SELECT 1 FROM information_schema.key_column_usage k
  WHERE k.table_name = c.table_name AND k.column_name = c.column_name
  AND k.table_schema = 'public'
);
```

## A09: Security Logging and Monitoring Failures

**What to check:**
- All business data tables have `fn_audit_trigger` attached
- `audit_log` table captures: operation, table_name, record_id, old_data, new_data, changed_by, changed_at
- No way to modify `audit_log` directly (INSERT only, no UPDATE/DELETE policies)

**How to check:**
```sql
-- Tables with audit triggers
SELECT event_object_table, trigger_name
FROM information_schema.triggers
WHERE trigger_name LIKE 'audit_%'
ORDER BY event_object_table;

-- Compare against list of business tables
```

## A10: Server-Side Request Forgery (SSRF)

**What to check:**
- Edge Functions that make external HTTP calls validate the URL
- No user-supplied URLs passed directly to `fetch()`
- Webhook endpoints validate the source

**How to check:**
```bash
grep -rn 'fetch(' supabase/functions/ | grep -v 'supabase'
# Any fetch not to Supabase should be reviewed
```
