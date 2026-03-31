---
name: code-review
description: Review PRs for Redoe OS against a manufacturing-specific checklist covering RLS security, design system compliance, naming conventions, and OWASP basics. Use when user says "review this PR", "code review", "check this code", invokes /code-review, or when reviewing changes before merge. Also runs automatically via Claude Code Action on every PR.
---

# Code Reviewer — Redoe OS PR Review

Reviews code changes against a Redoe-specific checklist. Advisory — posts comments but does NOT block merge. Humans make the final call.

## Step 1: Load Review Context

Read `references/redoe-review-checklist.md` for the full checklist with examples.

If the PR touches `supabase/`, also read:
- Schema Guardian's `references/schema-conventions.md` for naming rules
- The relevant RLS policies in `schema-v1.sql`

If the PR touches `apps/web/`, also read:
- The design system: `10_Business/Tooling/Redoe-Windsor/_Projects/Redoe-OS/_reference/design-system.md`
- UI strategy: `_reference/ui-strategy.md`

## Step 2: Read the Diff

Get the changed files:
```bash
git diff --name-only main...HEAD
```

Read each changed file. For large diffs, focus on:
1. New files (highest risk — no prior review)
2. Files touching RLS policies or auth
3. Files with financial data handling

## Step 3: Apply Checklist

### Database Changes (`supabase/`)
- [ ] RLS enabled on any new table
- [ ] RLS policies cover all required CRUD operations per role tier
- [ ] Audit trigger attached to business data tables
- [ ] snake_case naming everywhere
- [ ] No `DROP COLUMN` without migration plan
- [ ] Enums use lowercase values
- [ ] `created_at` and `updated_at` on all tables
- [ ] No `SECURITY DEFINER` functions unless justified (only `fn_audit_trigger` should be DEFINER)
- [ ] Financial data (costs, margins, revenue) restricted by role-based RLS
- [ ] No raw SQL strings — use parameterized queries

### Frontend Changes (`apps/web/`)
- [ ] CSS variables for colors (no hardcoded hex like `#1F4E79`)
- [ ] `font-mono` (JetBrains Mono) on numbers, codes, job IDs
- [ ] Touch targets >= 44px (shop floor) or >= 36px (desktop)
- [ ] No financial data exposed to shop floor role
- [ ] shadcn/ui components used (not custom HTML elements)
- [ ] Forms use react-hook-form + zod validation
- [ ] F738 referred to as "Work Order" in all UI text
- [ ] Types imported from `@redoe-os/types` (never hand-written `interface Job {}`)
- [ ] Dark mode renders correctly (slate-950 base, never pure black)

### Security
- [ ] No secrets committed (API keys, `service_role` key, connection strings)
- [ ] No `.env` files in the commit
- [ ] No `SECURITY DEFINER` functions without justification
- [ ] Parameterized queries only — no string interpolation in SQL
- [ ] Auth checks on all Edge Functions

### CODEOWNERS
- [ ] If PR touches `supabase/`, author is NOT Kevin (kevin cannot access database layer)
- [ ] Appropriate reviewers assigned per CODEOWNERS rules

### Performance
- [ ] No `SELECT *` in production queries
- [ ] No N+1 query patterns in data fetching
- [ ] Missing indexes flagged on filtered/joined columns
- [ ] `React.memo` on heavy list renderers

## Step 3b: AI Slop Detection (v9)

Check for patterns that indicate generic AI-generated code that wasn't customized for Redoe OS:

| Pattern | What to Flag | Severity |
|---------|-------------|----------|
| **Generic gradients** | `bg-gradient-to-r from-purple-500 to-blue-500` or similar decorative gradients with no design system justification | Should Fix |
| **Default shadcn theme** | Components using stock neutral palette instead of Redoe tokens (`--redoe-navy`, `--redoe-blue`, etc.) | Should Fix |
| **Placeholder data in commits** | "Lorem ipsum", "John Doe", "Acme Corp", "example@email.com", "Sample Project" in committed code (not test fixtures) | Must Fix |
| **Card soup** | 6+ identical card components in a grid with no hierarchy, differentiation, or real data source | Should Fix |
| **Dashboard widget theater** | Charts, gauges, or progress bars that look impressive but aren't connected to real Supabase queries | Must Fix |
| **Generic hero/welcome section** | "Welcome to [App Name]" with stock gradient, no real content or KPIs | Should Fix |
| **SaaS terminology** | "Tickets" instead of "Work Orders", "Projects" instead of "Jobs", "Technician" instead of "Moldmaker" | Must Fix |

**How to check:** Scan all new/modified `.tsx` and `.css` files for these patterns. Flag with specific file:line references.

**Why this matters:** Kevin (frontend) uses AI tools. If AI-generated code ships with stock styling and generic terminology, it undermines the NORAD aesthetic and confuses shop floor operators who see unfamiliar terms.

## Step 4: Output Review

Format the review as:

```
## Code Review — [PR title]

**Summary:** [2-3 sentences on what this PR does]

### Must Fix (blocks merge)
1. [file:line] — [issue description + suggested fix]

### Should Fix (recommended before merge)
1. [file:line] — [issue description]

### Suggestions (optional improvements)
1. [file:line] — [suggestion]

### Checklist
- Database: X/Y items checked — [PASS/FAIL]
- Frontend: X/Y items checked — [PASS/FAIL]
- Security: X/Y items checked — [PASS/FAIL]

**Verdict:** APPROVE / REQUEST CHANGES / COMMENT
```

Be direct. Steve reads fast — no fluff.

## CI Integration

Uses `anthropics/claude-code-action@v1` in `.github/workflows/claude-review.yml`:
- Triggers on every PR (opened, synchronize, reopened)
- Posts review as PR comment
- Uses Sonnet for cost efficiency (~$0.15/review)
- Advisory only — does NOT block merge

See `references/claude-code-action-setup.md` for configuration details.

## Review Readiness Dashboard (v8)

After code review completes, write to `_workspace/review-status.json`:
```json
{
  "code_review": {
    "completed": "2026-03-23T16:30:00Z",
    "commit": "<current HEAD short>",
    "verdict": "APPROVE",
    "must_fix_count": 0,
    "should_fix_count": 2,
    "suggestion_count": 3
  }
}
```
This is read by `/ship` to gate deployments. A `must_fix_count > 0` will block `/ship`.
