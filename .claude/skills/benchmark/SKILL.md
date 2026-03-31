---
name: benchmark
description: "Performance baseline for Redoe OS. Measures Core Web Vitals (LCP, CLS), JS bundle size, and page load times — especially on simulated shop floor WiFi. Stores baselines, compares before/after per PR, alerts on >20% regression. Use before /ship, after significant frontend changes, or when operators report slowness."
---

# /benchmark — Performance Baseline & Regression Detection

Measures what matters for a manufacturing app: can a shop floor operator on a WiFi tablet load the page in under 2 seconds? If a PR makes that worse, we catch it here.

**Team:** Steve (VP), Andy (backend), Kevin (frontend), Ben Wang.

## Usage

```
/benchmark                     — Measure all key pages, compare to baseline
/benchmark /jobs               — Measure a specific route
/benchmark --save              — Save current measurements as new baseline
/benchmark --compare feat/x    — Compare feature branch against main baseline
```

## What We Measure

### Core Web Vitals
| Metric | Target | Shop Floor Target | What It Means |
|--------|--------|-------------------|---------------|
| **LCP** (Largest Contentful Paint) | <2.5s | <2.0s | Time until the biggest visible element renders |
| **CLS** (Cumulative Layout Shift) | <0.1 | <0.05 | How much the page jumps around during load |
| **INP** (Interaction to Next Paint) | <200ms | <100ms | Response time when user taps/clicks |

### Bundle & Resource Metrics
| Metric | Target | What It Means |
|--------|--------|---------------|
| **Total JS bundle** | <500KB gzipped | JavaScript shipped to browser |
| **First load JS** | <200KB gzipped | JS needed for initial page render |
| **Total page weight** | <2MB | Everything: JS, CSS, images, fonts |
| **Font files** | <=3 files | DM Sans, JetBrains Mono, Outfit only |

### Page-Specific Targets
| Page | Tier | LCP Target | Notes |
|------|------|-----------|-------|
| `/` (HQ Dashboard) | Management | <2.5s | Complex — KPIs, entity cards, alerts |
| `/jobs` (Job List) | Management | <2.0s | Data table — paginated |
| `/jobs/[id]` (Job Detail) | Management | <2.0s | Single record |
| `/shopfloor/clock` (Time Clock) | Shop Floor | <1.5s | CRITICAL — operators use this 20x/day |
| `/shopfloor/jobs` (Job Allocation) | Shop Floor | <1.5s | Must be fast on tablet WiFi |

## How It Works

### Step 1: Start Dev Server
```bash
cd apps/web && pnpm dev
```
Wait for server ready (poll `http://localhost:3000`).

### Step 2: Run Measurements
Use Playwright MCP to open each page with performance tracing:

For each target page:
1. Open in browser with performance observer
2. Measure LCP, CLS, INP via PerformanceObserver API
3. Record total JS transferred (from Performance.getEntriesByType('resource'))
4. Record page load time (navigationStart to loadEventEnd)
5. Run TWICE and take the median (first run has cold cache, second is warm)

For simulated shop floor WiFi:
- Throttle to: 10 Mbps down, 2 Mbps up, 40ms RTT (typical plant WiFi)
- Test Shop Floor pages on throttled connection specifically

### Step 3: Compare Against Baseline
Read baseline from `_workspace/benchmarks.json`:

```json
{
  "version": "2026.03.2",
  "timestamp": "2026-03-27T12:00:00Z",
  "pages": {
    "/": { "lcp": 1.8, "cls": 0.02, "inp": 120, "js_kb": 380, "total_kb": 1200 },
    "/jobs": { "lcp": 1.2, "cls": 0.01, "inp": 80, "js_kb": 320, "total_kb": 900 },
    "/shopfloor/clock": { "lcp": 0.9, "cls": 0.0, "inp": 50, "js_kb": 180, "total_kb": 500 }
  },
  "bundle": { "total_js_gzip_kb": 420, "first_load_js_gzip_kb": 165 }
}
```

**Regression rules:**
- Any metric >20% worse than baseline: **WARN**
- LCP >3s on any page: **FAIL**
- Shop Floor page LCP >2s: **FAIL**
- JS bundle >500KB gzipped: **WARN**
- CLS >0.1 on any page: **FAIL**

### Step 4: Report

```
=========================================
BENCHMARK REPORT — Redoe OS
=========================================
Branch: feat/SPEC-012-job-list
Baseline: v2026.03.2 (2026-03-27)

Page Performance:
────────────────────────────────────────
/                   LCP 1.9s (+5%)    CLS 0.02  INP 125ms    OK
/jobs               LCP 1.4s (+17%)   CLS 0.01  INP 90ms     OK
/shopfloor/clock    LCP 1.0s (+11%)   CLS 0.00  INP 55ms     OK

Bundle Size:
────────────────────────────────────────
Total JS (gzip):    435KB (+3.6%)     OK
First Load JS:      172KB (+4.2%)     OK

Shop Floor WiFi Simulation (10/2 Mbps, 40ms):
────────────────────────────────────────
/shopfloor/clock    LCP 1.4s          PASS (< 2.0s target)
/shopfloor/jobs     LCP 1.6s          PASS (< 2.0s target)

VERDICT: PASS — no regressions above threshold
=========================================
```

## Saving Baselines

When `--save` is specified:
1. Run all measurements
2. Write to `_workspace/benchmarks.json`
3. Include git commit hash and version for traceability

**When to save a new baseline:**
- After shipping a new version to main
- After significant infrastructure changes (Next.js upgrade, new fonts, etc.)
- After intentional performance work

## Integration

- **`/qa`** — does not check performance (that's this skill's job)
- **`/ship`** — run `/benchmark` before shipping to catch perf regressions
- **`/canary`** — compares production against baseline post-deploy
- **`/design-review`** — flags heavy assets (images, fonts) that impact load time

## What This Catches

- JS bundle creep (adding heavy dependencies without noticing)
- Unoptimized images or fonts
- N+1 data fetching that slows page load
- Layout shift from late-loading components
- Shop floor pages too slow for tablet WiFi
- Performance regression introduced by new features
