---
name: canary
description: "Post-deploy monitoring for Redoe OS. After PR merge, watches the deploy for console errors, page failures, performance regressions, and runtime crashes. Keeps checking until confident the deploy is healthy. Use after /ship --land merges a PR, or manually after any production deploy."
---

# /canary — Watch the Deploy

After code ships, somebody needs to watch it land. This skill monitors the production deploy for errors, crashes, and regressions — then reports healthy or raises the alarm.

**Team:** Steve (VP), Andy (backend), Ben Wang.

## Usage

```
/canary                        — Monitor latest deploy (auto-detect production URL)
/canary https://redoe-os.vercel.app  — Monitor specific URL
/canary --pages /jobs,/shopfloor/clock  — Monitor specific pages only
/canary --duration 5m          — Monitor for 5 minutes (default: 3 minutes)
```

**When to run:**
- Automatically after `/ship --land` merges a PR
- After any manual production deploy
- When operators report issues after a release

---

## Before Starting

1. Get the production URL from environment or `_workspace/deploy-config.json`
2. Read the latest baseline from `_workspace/benchmarks.json` (for performance comparison)
3. Identify which pages were affected by the deployed changes:
   ```bash
   gh pr view --json files -q '.files[].path' | grep 'apps/web/src/'
   ```

---

## Monitoring Loop

### Phase 1: Deploy Health Check (30 seconds)

1. **Poll deploy status** (if Vercel):
   ```bash
   gh api repos/{owner}/{repo}/deployments --jq '.[0].statuses_url'
   ```
   Wait until deployment status is "success". If "failure" or "error": **ALERT immediately.**

2. **HTTP health check** on production URL:
   - GET the root URL — expect 200
   - GET each affected page — expect 200
   - If any return 500/503: **ALERT — deploy is broken**

### Phase 2: Page Verification (1-2 minutes)

For each affected page (or all key pages if changes are broad):

1. **Open in browser** via Playwright MCP
2. **Check console** for JavaScript errors:
   - Filter out known noise (browser extensions, analytics)
   - Any `Error`, `TypeError`, `ReferenceError` = finding
   - Any uncaught promise rejection = finding
3. **Visual smoke test:**
   - Page renders (not blank white screen)
   - Key elements present (sidebar, KPI cards, data table — depending on page)
   - No "undefined" or "null" visible in data fields
4. **Performance spot-check:**
   - Compare LCP against baseline (from `/benchmark`)
   - If >30% slower than baseline: **WARN**

### Phase 3: Interaction Test (1 minute)

On the most critical pages:

1. **Click primary action** (e.g., navigate to a job, open a filter, submit a form)
2. **Check for runtime errors** after interaction
3. **Verify data loads** (not empty state when data should be present)

For Shop Floor pages specifically:
- Verify touch targets are responsive
- Verify time clock page loads and is interactive
- This is the highest-traffic surface — if it breaks, operators go back to paper

---

## Alert Levels

| Level | Trigger | Action |
|-------|---------|--------|
| **CRITICAL** | Deploy failed, 500 errors, blank pages | Immediate alert. Recommend rollback. |
| **HIGH** | Runtime JS errors on key pages | Alert with specific error + affected page |
| **MEDIUM** | Performance regression >30% | Warn — may need hotfix |
| **LOW** | Console warnings, minor visual glitches | Note in report — fix in next PR |
| **HEALTHY** | All checks pass | Confirm deploy is clean |

---

## Output

```
=========================================
CANARY REPORT — Redoe OS
=========================================
Deploy:     v2026.03.3
URL:        https://redoe-os.vercel.app
Duration:   3 minutes
Pages:      6 checked

Health Checks:
────────────────────────────────────────
Deploy status:      SUCCESS
Root (200):         OK
/jobs (200):        OK
/shopfloor/clock:   OK

Console Errors:     0
Runtime Crashes:    0

Performance vs Baseline:
────────────────────────────────────────
/jobs          LCP 1.3s (baseline: 1.2s, +8%)     OK
/shopfloor     LCP 1.0s (baseline: 0.9s, +11%)    OK

Interaction Tests:
────────────────────────────────────────
Navigate to job:       OK
Filter job list:       OK
Time clock load:       OK

VERDICT: HEALTHY — deploy is clean
=========================================
```

If issues found:
```
VERDICT: HIGH ALERT — 2 findings

Finding 1: TypeError on /jobs when filter is "All"
  Console: "Cannot read properties of undefined (reading 'map')"
  Steps to reproduce: Navigate to /jobs, click "All" filter
  Recommendation: Hotfix — null check on job list response

Finding 2: Performance regression on /shopfloor/clock
  LCP: 2.4s (baseline: 0.9s, +167%)
  Possible cause: New font file not cached
  Recommendation: Check font loading strategy
```

---

## Integration

- **`/ship --land`** — auto-invokes `/canary` after merge + deploy
- **`/benchmark`** — provides the baseline for performance comparison
- **`/investigate`** — if canary finds a bug, hand off to `/investigate`
- **`/retro`** — if canary catches a production issue, feed into retro

---

## What This Catches

- Deploy failures that nobody notices until Monday morning
- Runtime errors that compile fine but crash in production
- Performance regressions from unoptimized new code
- Data display bugs (undefined, null, empty where data should exist)
- Shop floor pages broken (highest operational impact)
- Silent failures (page loads but core feature doesn't work)
