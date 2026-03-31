---
name: regression
description: Run the full Redoe OS test suite and report results. Covers pgTAP database tests, RLS audit, type freshness, lint, TypeScript type-check, Vitest unit tests, and Playwright E2E. Use when user says "run tests", "run regression", "check the build", invokes /regression, or needs to verify everything passes before merging. Also runs automatically via GitHub Actions on every PR.
---

# Regression Runner — Full Test Suite for Redoe OS

Runs all quality checks in parallel, collects results, and reports a unified pass/fail status. Works locally (via slash command) and in CI (via GitHub Actions).

## Step 0: Test Framework Bootstrap (v8)

Before running any tests, verify the test infrastructure exists. If a new developer (or Andy starting fresh) runs `/regression`, it should work — not fail with "command not found."

**Check these prerequisites:**

```bash
# 1. Supabase CLI installed?
supabase --version || echo "MISSING: supabase CLI"

# 2. pgTAP tests directory exists with at least one test?
ls supabase/tests/*.sql 2>/dev/null | wc -l

# 3. Vitest configured?
test -f apps/web/vitest.config.ts || test -f apps/web/vite.config.ts

# 4. Playwright installed?
npx playwright --version 2>/dev/null || echo "MISSING: playwright"

# 5. Dependencies installed?
test -d node_modules || echo "MISSING: run pnpm install"
```

**If anything is missing, auto-scaffold:**

| Missing | Action |
|---------|--------|
| `supabase/tests/` empty | Create `supabase/tests/00_setup.sql` with pgTAP initialization + one smoke test |
| `vitest.config.ts` missing | Create minimal config importing from `@redoe-os/config` |
| Playwright not installed | Run `pnpm --filter web exec playwright install chromium` |
| `node_modules` missing | Run `pnpm install` |
| No `TESTING.md` | Create `TESTING.md` documenting test commands and conventions |

**After bootstrap:** Continue to Step 1 normally. Log what was scaffolded:
```
Bootstrap: Created supabase/tests/00_setup.sql (pgTAP init)
Bootstrap: Installed Playwright chromium
Continuing to test execution...
```

**Never fail silently.** If bootstrap can't fix a missing prerequisite (e.g., Supabase CLI not installed), print clear instructions:
```
BLOCKED: Supabase CLI not found.
Install: brew install supabase/tap/supabase (Mac) or scoop install supabase (Windows)
Then re-run /regression.
```

## Step 1: Determine Scope

Check which files changed to decide what to run:
```bash
git diff --name-only main...HEAD
```

| Changed path | Tests to run |
|-------------|-------------|
| `supabase/**` | pgTAP, RLS audit, type freshness |
| `apps/web/**` | Lint, type-check, Vitest, Playwright E2E |
| `packages/**` | Type-check, Vitest |
| Both | All tracks |
| Docs/config only | Lint only |

If invoked with `/regression full`, run everything regardless of changes.

## Step 2: Run Test Tracks

Run these tracks in parallel where possible:

### Track 1: Database (supabase changes)
```bash
supabase db reset                    # Apply all migrations + seed
supabase test db                     # Run pgTAP tests
```

### Track 2: RLS Audit (supabase changes)
Query PostgreSQL directly for tables without RLS:
```sql
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
AND tablename NOT IN (
  SELECT relname FROM pg_class WHERE relrowsecurity = true
);
```
Any result = FAIL (unless table is in the exceptions list).

### Track 3: Type Freshness (supabase changes)
```bash
supabase gen types typescript --local > /tmp/types_check.ts
diff packages/types/database.ts /tmp/types_check.ts
```
Any diff = FAIL (types are stale, need regeneration).

### Track 4: Lint + Type-check (frontend changes)
```bash
pnpm turbo run lint type-check
```

### Track 5: Unit Tests (frontend changes)
```bash
pnpm turbo run test
```

### Track 6: E2E Tests (frontend changes)
```bash
pnpm --filter web exec playwright test
```

## Step 3: Collect Results

Parse exit codes from each track. Build summary table:

```
## Regression Results — [date] [scope]

| Track | Status | Duration | Details |
|-------|--------|----------|---------|
| pgTAP | PASS/FAIL | Xs | N/N tests |
| RLS Audit | PASS/FAIL | Xs | N tables checked |
| Type Freshness | PASS/FAIL | Xs | Types match/stale |
| Lint | PASS/FAIL | Xs | N warnings |
| TypeScript | PASS/FAIL | Xs | N errors |
| Vitest | PASS/FAIL | Xs | N/N tests |
| Playwright | PASS/FAIL | Xs | N/N flows |

**Result: ALL PASSED / N FAILED**
```

## Step 4: Report

- **Local:** Print summary to terminal
- **CI:** Post as PR comment (upsert — update existing bot comment to avoid spam)

If failures exist, include the first 20 lines of each failure output and a direct link to the full CI log.

## CI Integration

Three separate GitHub Actions workflows handle this:

### `.github/workflows/ci.yml`
- Triggers on every PR to `main`
- Runs lint, type-check, Vitest in parallel via Turborepo
- Includes type freshness check

### `.github/workflows/db-qa.yml`
- Triggers on PRs changing `supabase/**`
- Runs Schema Guardian first, then pgTAP + RLS audit
- Posts database-specific results as PR comment

### `.github/workflows/e2e.yml`
- Triggers on PRs changing `apps/web/**`
- Builds frontend, starts local Supabase, runs Playwright
- Uploads failure screenshots as artifacts

See `references/` for complete workflow YAML templates.

## Local Usage

```bash
pnpm qa:all      # Run everything
pnpm qa:db       # Database only (supabase reset + pgTAP)
pnpm qa:schema   # Schema Guardian only
pnpm qa:types    # Type freshness only
```

## Design Decisions

- **3 separate workflows, not 1.** Frontend-only PRs don't wait for Supabase startup (~30-60s savings).
- **No SupaShield dependency.** Direct `pg_class.relrowsecurity` query — simpler, no third-party risk.
- **Bot comment upserts.** Find existing comment by marker text, update it. No comment spam.
- **Type freshness is a hard fail.** Stale types = runtime errors. Non-negotiable.
