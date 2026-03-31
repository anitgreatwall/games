---
name: security-audit
description: Deep security scan for Redoe OS — OWASP Top 10, RLS policy gaps, exposed secrets, vulnerable dependencies. Use when user says "security audit", "scan for vulnerabilities", "check RLS", "check secrets", invokes /security-audit, or before production deployments. Also runs weekly via GitHub Actions cron.
---

# Security Auditor — Deep Scan for Redoe OS

Comprehensive security scan covering OWASP Top 10 (mapped to Supabase), RLS policy completeness, secrets detection, and dependency vulnerabilities. Posts findings as a GitHub Issue (not a PR comment — security findings are repo-wide).

## Step 1: RLS Completeness Audit

Query all public tables and check RLS status:

```sql
SELECT c.relname AS table_name,
       c.relrowsecurity AS rls_enabled,
       (SELECT COUNT(*) FROM pg_policies p WHERE p.tablename = c.relname) AS policy_count
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public' AND c.relkind = 'r'
ORDER BY c.relname;
```

For each table:
- RLS enabled + policies = PASS
- RLS enabled + zero policies = CRITICAL (deny-all — silent data loss)
- RLS not enabled = check against `references/rls-exceptions.md`
  - In exceptions list with justification = PASS
  - NOT in exceptions list = CRITICAL

## Step 2: Policy Gap Analysis by Tier

For each RLS-enabled table, verify policies cover all 4 security tiers:

| Tier | Expected SELECT | Expected INSERT | Expected UPDATE | Expected DELETE |
|------|----------------|----------------|----------------|----------------|
| Shop Floor | Own plant, no costs | Own records | Own records | BLOCKED |
| PM/Leads | Own plant, with costs | Own records | Own records | BLOCKED |
| Finance | Own plant, full | All in scope | Status changes | BLOCKED |
| Management | ALL plants, full | All | All | Restricted |

Flag missing policies per operation per tier. Read `references/owasp-supabase-mapping.md` for detailed checks.

## Step 3: OWASP Top 10 Scan (Supabase-Specific)

| OWASP | Check | How |
|-------|-------|-----|
| A01 Broken Access Control | Missing `auth.uid()` or `auth.jwt()` in RLS | Grep policies for auth references |
| A02 Cryptographic Failures | Plaintext secrets in migrations | Grep for API key patterns |
| A03 Injection | Raw SQL in Edge Functions | Grep for template literals in SQL |
| A04 Insecure Design | `SECURITY DEFINER` bypass | Grep functions for DEFINER |
| A05 Misconfiguration | Exposed `service_role` key | Grep frontend for service_role |
| A06 Vulnerable Components | Known CVEs | `pnpm audit --json` |
| A07 Auth Failures | Weak auth config | Check Supabase auth settings |
| A08 Data Integrity | Missing FK constraints | Query pg_constraint |
| A09 Logging Failures | Tables without audit triggers | Cross-reference trigger list |
| A10 SSRF | External calls without URL validation | Grep Edge Functions |

## Step 3b: STRIDE Threat Model (v9)

After OWASP checks, apply the STRIDE framework to model threats systematically. For each category, identify concrete threats specific to Redoe OS:

| STRIDE Category | What to Look For | Redoe-Specific Checks |
|----------------|-----------------|----------------------|
| **S**poofing | Can someone impersonate another user? | JWT manipulation, tier escalation (Shop Floor → Management), shared kiosk identity theft |
| **T**ampering | Can data be modified in transit or at rest? | RLS bypass via direct API, cost data manipulation, labour entry backdating |
| **R**epudiation | Can actions be denied? | Missing audit_log entries on financial tables, unsigned approvals |
| **I**nformation Disclosure | Can unauthorized data leak? | Cost data visible to Shop Floor, customer data in error messages, verbose Supabase errors |
| **D**enial of Service | Can the system be overwhelmed? | Unbounded queries without pagination, missing rate limits on Edge Functions, large file uploads |
| **E**levation of Privilege | Can a lower-tier user gain higher access? | RLS policy gaps between tiers, SECURITY DEFINER escalation, admin routes without auth check |

### Confidence Scoring (v9)

For each finding, assign a confidence score 1-10:
- **8-10:** High confidence — clear evidence, exploitable. **REPORT.**
- **5-7:** Medium confidence — possible issue, needs verification. **REPORT with caveat.**
- **1-4:** Low confidence — theoretical, unlikely in practice. **SUPPRESS** (do not include in report).

This reduces false positive noise. Only surface findings with confidence >= 5.

### Known False Positives (suppress automatically)

1. `anon` key in frontend code (this is Supabase's public key — by design)
2. RLS not enabled on `schema_migrations` table (Supabase internal)
3. `SECURITY DEFINER` on `fn_audit_trigger` (required for cross-user audit logging)
4. `.env.example` file (contains placeholder values, not real secrets)
5. Test fixtures with hardcoded UUIDs (test data, not real credentials)
6. Supabase client initialization with `NEXT_PUBLIC_SUPABASE_URL` (public by design)
7. `service_role` in `supabase/seed.sql` (runs server-side only, never in client bundle)

## Step 4: Secrets Scan

Run `scripts/secrets_scan.sh` or manually grep for:

**IMPORTANT:** Scan ALL frontend file types — Redoe OS uses static HTML + vanilla JS, not just TypeScript.

```bash
# File types to scan (MUST include .html — this is where Redoe OS frontend lives)
INCLUDES="--include=*.ts --include=*.tsx --include=*.js --include=*.html --include=*.sql --include=*.env --include=*.yml --include=*.json"

# JWT tokens
grep -rn 'eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\.' $INCLUDES

# Supabase keys
grep -rn 'sb_[a-zA-Z0-9]' $INCLUDES

# service_role in frontend (scan ALL of apps/, not just apps/web/)
grep -rn 'service_role' apps/ | grep -v 'REDOE-supabase-svr'

# Connection strings
grep -rn 'postgresql://' $INCLUDES

# Known vendor API key patterns
grep -rn 'ANTHROPIC_API_KEY\|OPENAI_API_KEY\|sk-[a-zA-Z0-9]' $INCLUDES

# Hardcoded API keys with literal values (NOT env var references)
grep -rni 'api.key.*=.*'"'"'[a-zA-Z0-9_-]\{10,\}'"'"'' --include='*.html' --include='*.js' --include='*.ts' | grep -v 'process\.env'

# Hardcoded passwords/tokens/secrets with literal values
grep -rniE '(password|token|secret)\s*[:=]\s*['"'"'"][^'"'"'"]{8,}['"'"'"]' --include='*.html' --include='*.js' --include='*.ts' | grep -v 'process\.env' | grep -v '\.example'

# .env files committed
find . -name '.env' -not -path './node_modules/*'
```

Also verify `.gitignore` includes: `.env`, `.env.local`, `.env.production`

## Step 5: Dependency Audit

```bash
pnpm audit --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for vuln in data.get('advisories', {}).values():
    severity = vuln.get('severity', 'unknown')
    title = vuln.get('title', 'Unknown')
    module = vuln.get('module_name', 'Unknown')
    print(f'{severity.upper()}: {module} — {title}')
"
```

## Step 6: Claude Code Self-Security Check

Audit the Claude Code configuration itself for security issues. Read `references/threat-patterns.md` for the full pattern database.

**Checks:**

1. **settings.json permissions audit:**
   - Verify deny list covers: `git push --force`, `git reset --hard`, `git clean -f`, `.env` read/write
   - Check allow list for overly broad patterns (e.g., `Bash(*)`)
   - Flag any wildcard permissions that could be exploited

2. **Skills directory integrity:**
   - List all files in `.claude/skills/` — flag any unexpected or unreviewed skill
   - Check SKILL.md files for prompt injection patterns: "ignore previous", "override", "forget instructions", "disregard"
   - Check skills for external URL references (fetch/curl to non-project domains)

3. **Hook safety:**
   - Verify all hooks in settings.json use safe commands
   - Flag hooks that make network calls or modify files destructively

4. **MCP server audit:**
   - Check for any configured MCP servers (Redoe OS currently uses zero)
   - If MCP servers found: audit their package dependencies and permissions

5. **Memory file review:**
   - Check memory files for instruction-like content that could override project rules
   - Verify memory content is informational only, not directive

**Output:** List findings with confidence scores (same 1-10 scale as STRIDE).

## Step 7: Output Report

Format as a security report with severity levels:

```
## Security Audit Report — [date]

### CRITICAL (fix immediately)
1. [finding] — [location] — [remediation steps]

### HIGH (fix before next deployment)
1. [finding] — [remediation]

### MEDIUM (fix within sprint)
1. [finding] — [remediation]

### LOW (track for future)
1. [finding] — [remediation]

### Audit Coverage
| Category | Checked | Result |
|----------|---------|--------|
| RLS completeness | X/Y tables | PASS/FAIL |
| Policy gap analysis | X tiers checked | N gaps |
| OWASP Top 10 | X/10 categories | N findings |
| Secrets scan | N files scanned | CLEAN/N items |
| Dependencies | N packages | N vulnerabilities |
| Audit triggers | X/Y tables | PASS/FAIL |
```

## CI Integration

Weekly cron in `.github/workflows/claude-review.yml`:
- Schedule: Sunday 6am UTC (`cron: '0 6 * * 0'`)
- Also available as `workflow_dispatch` for on-demand runs
- Posts findings as a GitHub Issue (not PR comment)
- Labels: `security`, `audit`, severity level

## Local Usage

```bash
/security-audit          # Full scan
/security-audit rls      # RLS-only scan
/security-audit secrets  # Secrets-only scan
/security-audit deps     # Dependencies only
```

## Design Decisions

- **Secrets scan runs per-PR.** It's just grep — runs in ~2 seconds. Added to CI alongside Code Reviewer.
- **Deep audit (RLS, deps, OWASP) stays weekly.** These require Supabase and are slow/noisy on every PR.
- **GitHub Issue, not PR comment.** Security findings are repo-wide, not PR-specific. Issues track remediation.
- **RLS exceptions documented.** Prevents alert fatigue on intentional decisions (lookup tables without RLS).
