# Redoe OS Code Review Checklist — Full Reference

## Naming Conventions (MUST PASS)

Read `qa/references/naming-conventions.md` for the full ruleset. Check all new/renamed files:

- [ ] All new HTML files use `kebab-case.html` (no underscores, no camelCase, no cryptic codes like `a8` or `t38`)
- [ ] All new folders use lowercase kebab-case (exception: `docs/` top-level categories are UPPERCASE)
- [ ] No junk files (`New Text Document.*`, `Untitled*`, `Copy of *`, backup/copy suffixes)
- [ ] No spaces or non-ASCII characters in filenames
- [ ] Branch name follows `type/SPEC-NNN-slug` or `type/description` pattern
- [ ] Spec/decomp files follow `SPEC-NNN-slug.md` / `DECOMP-NNN-slug.md` convention
- [ ] SQL migrations follow `YYYYMMDD_snake_description.sql` convention
- [ ] No mixed separators in a single filename (e.g., `AI_MM-Manual.html` mixes `_` and `-`)

If any cryptic names exist, flag: "What does `{name}` stand for? Needs a descriptive kebab-case replacement."

## Database Layer

### RLS Policy Completeness
Every table accessible via the Supabase client MUST have:
1. `ENABLE ROW LEVEL SECURITY` statement
2. At least one policy per CRUD operation the app performs on that table
3. Policies that respect the 4-tier security model:

| Tier | Roles | Plant Access | Cost/Financial Data |
|------|-------|-------------|-------------------|
| Shop Floor | cnc_operator, moldmaker, edm_operator, inspector | Own plant only | BLOCKED |
| PM/Leads | pm, engineering_mgr, scheduler, plant_mgr | Own plant only | Hours + variance |
| Finance | finance, buyer | Own plant only | Full access |
| Management | gm, vp | ALL plants | Full access |

### Anti-Patterns to Flag
- `USING (TRUE)` on tables with sensitive data — only appropriate for machine_events, machine_alerts, labour hours (no costs)
- `SECURITY DEFINER` on any function except `fn_audit_trigger` — bypasses RLS
- Missing `WHERE plant_id = ...` check in plant-scoped policies
- Policies that check `role` but not `plant_id` — allows cross-plant data leakage
- No `auth.uid()` or `auth.jwt()` check — means anon access

### Naming Violations (Common Mistakes)
- camelCase columns: `jobType` should be `job_type`
- Uppercase enum values: `'Running'` should be `'running'`
- Missing `fn_` prefix on functions
- Table names singular instead of plural: `job` should be `jobs`
- Trigger names not following convention: should be `audit_<table>` or `trg_<description>`

### Data Type Mistakes
- `TIMESTAMP` without TZ — always use `TIMESTAMPTZ`
- `VARCHAR(n)` — use `TEXT` unless there's a specific constraint reason
- `FLOAT` for money — use `DECIMAL(14,2)`
- `INT` for high-volume IDs — use `BIGSERIAL` for tables like `machine_events`

## Frontend Layer

### Design System Violations
- Hardcoded colors: `color: #1F4E79` should be `text-primary` or `bg-primary`
- Wrong font on numbers: job IDs, costs, hours must use `font-mono` (JetBrains Mono)
- Pure black backgrounds: `bg-black` should be `bg-slate-950`
- Missing glassmorphism on management views: `bg-card/60 backdrop-blur-xl border border-white/10`
- Custom components instead of shadcn/ui: `<input>` should be `<Input>`, `<select>` should be `<Select>`

### Shop Floor Rules
If the view targets shop floor operators:
- No sidebar — full-screen content only
- Three-screen max: Select → Act → Confirm
- Touch targets: 56px primary actions, 44px minimum everything
- No financial data visible (costs, margins, revenue, hourly rates)
- Font size minimum 16px body text
- No glassmorphism effects (performance on kiosk hardware)

### F738 Naming
The database table is `requirement_forms` but ALL UI must say "Work Order":
- Button: "New Work Order" (not "New F738")
- Header: "Work Order #WO-2026-001"
- Status: "Work Order approved"
- Only exception: internal documentation and code comments

### Type Safety
- Types MUST come from `@redoe-os/types` (auto-generated from Supabase schema)
- Never hand-write: `interface Job { id: string; ... }` — this drifts from schema
- `any` type requires a comment explaining why (flag if no comment)
- Zod schemas for form validation must match the database constraints

## Security Layer

### Secrets Detection Patterns
Flag these patterns in any committed file:
- `eyJ` followed by base64 (JWT tokens)
- `sb_` or `supabase` followed by long alphanumeric string (Supabase keys)
- `service_role` anywhere in frontend code
- `postgresql://` connection strings
- `.env` files without `.gitignore` coverage
- `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or similar in source

### OWASP Quick Checks
- A01 (Access Control): RLS policies exist and are restrictive by default
- A03 (Injection): No template literals in SQL: `` `SELECT * FROM ${table}` `` — use parameterized queries
- A05 (Misconfiguration): Supabase anon key used correctly (read-only public data only)
- A07 (Auth): Session timeout configured, password policy meets standards

## Business Logic

### Labour Entry Flow
Status must follow: DRAFT → SUBMITTED → APPROVED → REJECTED → LOCKED → SAP sync
- "Job 500" (nonproductive) entries require mandatory comments
- "RTRI" entries require mandatory comments
- Workers can only submit their own entries (RLS enforced)
- Supervisors can only approve entries for their department

### Revenue Recognition
Three-trigger model: T1 (First Trial ~89%), T2 (Ship Mold ~4%), T3 (Tuning ~7%)
- Code must not allow recognizing revenue outside these triggers
- Tuning reserve (FNG: 8% "MRR8") must be handled as deferred revenue

### Cost Types
Must use the `cost_type` enum: labour, material, outsource, tariff, freight, tuning, financing, overhead, other
- No free-text cost categories
- Tariff amounts calculated correctly (percentage of base cost)
