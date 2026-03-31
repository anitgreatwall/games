---
name: qa
description: "One-command quality gate for Redoe OS (v8). Runs all checks sequentially — schema validation, RLS audit, security scan, code review, test generation, and browser verification — then reports a single pass/fail. Writes to Review Readiness Dashboard for /ship gating. Use when anyone says 'run qa', 'check the code', 'is this safe to push', invokes /qa, or before any merge to main. This is the only QA command the team needs. Plug and play."
---

# QA — Redoe OS Quality Gate

Single command. Runs everything. Reports pass/fail. If it finds problems, it suggests fixes (or fixes them automatically if asked).

**Team:** Steve (VP), Andy (backend), Ben Wang. None are professional developers. This must be black-box simple.

## How to Use

```
/qa              — Full check (all 6 stages)
/qa quick        — Schema + secrets only (~30 seconds)
/qa fix          — Run full check, then auto-fix everything it can
```

## Pipeline (runs sequentially)

### Stage 0: Naming Lint
Check that all new or renamed files follow the Redoe OS naming conventions.
- Read `references/naming-conventions.md` for the full ruleset
- Get changed files: `git diff --name-only main...HEAD`
- For each new or renamed file, check:
  - **HTML files:** must be `kebab-case.html`, minimum 2 words, descriptive (not cryptic codes like `a8.html`)
  - **SQL migrations:** must match `YYYYMMDD_snake_description.sql`
  - **JS/TS source:** must be `kebab-case.js/ts` (or `PascalCase.tsx` for React components)
  - **Folders:** must be lowercase kebab-case (exception: `docs/` top-level categories are UPPERCASE)
  - **Banned patterns:** no spaces, no `New Text Document.*`, no `-backup`/`-copy`/`-old` suffixes, no single-char/number-only names, no mixed separators, no non-ASCII characters in filenames
- If violations found:
  - **FAIL** this stage
  - List each violation with the specific rule broken
  - Suggest the correct name: `"Rename AI_MM.html → ai-material-search.html"`
- If running `/qa fix`: auto-rename with `git mv` and re-stage

**For `/qa quick`:** Stage 0 still runs (fast, no external tools needed).

### Stage 1: Schema Guardian
Validate all SQL migrations for naming conventions, RLS presence, audit triggers, and breaking changes.
- Read `.claude/skills/schema-guardian/SKILL.md` and follow its steps
- If any FAIL: stop pipeline, report, suggest fix

### Stage 2: Security Scan
Check for exposed secrets, service_role leaks, and .env files.
- Run the checks from `.claude/skills/security-audit/SKILL.md` (Steps 4-5 only — secrets + deps)
- If CRITICAL finding: stop pipeline, report immediately

### Stage 3: RLS Audit
Verify all tables have appropriate Row Level Security.
- Run the RLS completeness check from `.claude/skills/security-audit/SKILL.md` (Steps 1-2)
- Cross-reference against `.claude/skills/security-audit/references/rls-exceptions.md`
- If tables missing RLS without exception: FAIL

### Stage 4: Code Review
Review changed files against the Redoe checklist.
- Get changed files: `git diff --name-only main...HEAD` (or `git diff --cached` if pre-commit)
- Read `.claude/skills/code-review/SKILL.md` and apply the checklist
- Report issues but don't block — these are advisory

### Stage 5: Test Coverage Check
Verify that new RLS policies and functions have corresponding pgTAP tests.
- Compare policies/functions in migrations against test files in `supabase/tests/`
- If gaps found: offer to generate tests using `.claude/skills/test-gen/SKILL.md`

<GATE name="pre-browser-check">
STOP. Verify Stages 1-5 all completed. If any CRITICAL or FAIL result in Stages 1-3: DO NOT proceed to browser verification. Fix the blocking issue first — browser testing on broken schema/security/RLS is wasted effort.
</GATE>

### Stage 6: Browser Verification (Three-Layer Architecture)
The feature must actually WORK, not just compile. This is the stage that separates good from best-in-class.

**Only runs when frontend files changed** (`apps/` modified in diff).

**Three-layer detection — structured checks first, screenshots as last resort:**

```
Layer 1: DOM Assertions (zero tokens, <1s)     → catches 80% of issues
Layer 2: Computed Style Audit (zero tokens)     → catches 15% of issues
Layer 3: Screenshot (high tokens, slow)         → only for visual regression / new pages
```

**How it works:**

#### Step 1: Open the page
- For static HTML apps: open via `file:///` or local HTTP server
- For dev server apps: `cd apps/web && pnpm dev` (background), poll until ready
- Navigate to the page the feature affects (read from SPEC acceptance criteria)

#### Step 2: Layer 1 — DOM Assertions (run `scripts/qa-dom-audit.js`)
Run the automated DOM audit script. It returns structured JSON (not screenshots):

```bash
node scripts/qa-dom-audit.js <url-or-file-path>
```

**What Layer 1 checks (from DOM API, exact values):**
| Check | Method | Severity |
|-------|--------|----------|
| Touch targets ≥ 44px (56px shop floor) | `getBoundingClientRect()` | CRITICAL |
| Console errors = 0 | `page.on('console')` | CRITICAL |
| Content loaded (not empty) | `document.body.innerText.length` | CRITICAL |
| Broken images | `img[naturalWidth=0]` | HIGH |
| Keyboard accessible | focusable element count | HIGH |
| Page title present | `document.title` | MEDIUM |

**What Layer 2 checks (from Computed Styles, exact values):**
| Check | Method | Severity |
|-------|--------|----------|
| Fonts: only DM Sans / JetBrains Mono | `getComputedStyle().fontFamily` | HIGH |
| Spacing: 4px grid compliance | `padding/margin % 4 === 0` | HIGH |
| Contrast ≥ 4.5:1 WCAG AA | luminance ratio calculation | CRITICAL |
| Status: color + icon + text (not color alone) | DOM structure check | HIGH |

**Design tokens reference:** `.claude/skills/qa/references/design-tokens.json`

The script outputs JSON like:
```json
{
  "summary": { "totalChecks": 10, "passed": 8, "failed": 2, "failures": ["fonts", "contrast"] },
  "layer1_dom": { "touchTargets": { "pass": true }, "consoleErrors": { "pass": true, "count": 0 } },
  "layer2_style": { "fonts": { "pass": false, "violations": ["arial"] }, "contrast": { "pass": false, "violations": [...] } }
}
```

This JSON costs **~200-500 tokens** vs **~3,000-6,000 tokens** for a screenshot. Same information, 10x cheaper.

#### Step 3: Evaluate Layer 1+2 results
- If ALL checks pass → **PASS Stage 6** (no screenshot needed)
- If CRITICAL failures → fix the code, re-run script (up to 3 retries)
- If HIGH failures → note in report, fix before merge

#### Step 4: Layer 3 — Screenshot (only when needed)
Take a screenshot ONLY in these cases:
1. **New page** (first time this page has been QA'd — need visual baseline)
2. **Major layout refactor** (structural changes where DOM checks can't capture "does it look right")
3. **User explicitly requests**: `/qa visual` forces screenshot mode
4. **Layer 1+2 can't diagnose** a reported bug (runtime visual glitch)

When screenshot IS taken:
- Use Playwright to capture at 768x1024 (tablet viewport)
- Focus on the specific area of concern, not full page
- Verify layout, visual hierarchy, data rendering

#### Step 5: Layer 1.5 — Interaction Audit (run `scripts/qa-interaction-audit.js`)
After design compliance passes, **automatically click through every interactive element**.
This is NOT manual — the script does it:

```bash
node scripts/qa-interaction-audit.js <url-or-file-path>
```

**What it does:**
- Finds all interactive elements: buttons, tabs, toggles, pills, links, dropdowns
- Clicks each one sequentially, waits 350ms for animations to settle
- After each click, checks:
  - Did the DOM respond? (content change, class toggle, aria-expanded flip)
  - Did the layout explode? (viewport overflow, elements jumping >50px)
  - Did content disappear? (body text length dropped significantly)
  - Any new console errors triggered by the click?
  - Are toggle states consistent? (aria-expanded matches visible state)

**Output:** JSON with per-element results:
```json
{
  "summary": { "elementsClicked": 14, "passed": 12, "failed": 2 },
  "expectedElements": { "total": 6, "found": 5, "missing": ["date-picker"] },
  "interactions": [
    { "selector": "button.tab-active", "action": "click", "pass": true },
    { "selector": "button.filter-date", "action": "click", "pass": false,
      "reason": "Content disappeared after click (body text 2400→0 chars)" }
  ]
}
```

**Route manifest:** Read `scripts/qa-routes.json` for the list of pages to test.
If SPEC acceptance criteria specify particular pages, test those. Otherwise, test ALL routes in the manifest that are affected by the current diff.

**Expected-element assertion:**
The script also reads `qa-routes.json` and checks that every expected interactive element for the matched route actually exists in the DOM. This catches **missing features**, not just broken ones:
- Route says the page should have a `date-picker` → script checks it exists and is visible
- Route says `data-table-sort` → script checks sortable column headers are present
- Output: `"Expected elements: 5/6 found. MISSING: date-picker"`
- Missing expected elements = **FAIL** (a feature didn't get built or got accidentally removed)

#### Step 5b: Functional Verification
After interaction audit passes, verify the feature-specific user flow:
- Verify data loads (not empty state when data should be present)
- Check responsive: resize to tablet (1024px) if Shop Floor tier
- Confirm SPEC acceptance criteria are met

#### Step 6: Self-healing loop
```
Run DOM audit (L1+L2) → Issues found?
  YES → Fix code → Re-run audit → Still broken?
    YES → Fix again (up to 3x) → Still broken? → FAIL, escalate
    NO → Continue
  NO → Run interaction audit (L1.5) → Issues found?
    YES → Fix → Re-run (up to 3x)
    NO → Functional verify → Bug found?
      YES → Fix → Re-test (up to 3x)
      NO → PASS Stage 6
```

#### Step 7: Cleanup
Kill any dev server processes. Report PASS or FAIL.

**Priority classification (unchanged):**

**Priority 1 — CRITICAL (block PR if violated):**
- Contrast 4.5:1 minimum on all text (WCAG AA) — *detected by Layer 2*
- Touch targets 44x44px minimum (56px for shop floor) — *detected by Layer 1*
- 8px spacing grid used — *detected by Layer 2*
- No hover-only interactions — *detected by Layer 2*
- Keyboard navigable — *detected by Layer 1*

**Priority 2 — HIGH (flag in PR, fix before merge):**
- Font: DM Sans / JetBrains Mono only — *detected by Layer 2*
- Colors: Redoe palette only — *detected by Layer 2*
- Status indicators: color + icon + text — *detected by Layer 2*
- No financial data on Shop Floor tier — *requires functional test*
- Layout: no sidebar for Shop Floor — *requires functional test*

**Priority 3 — MEDIUM (advisory, note in PR):**
- Animations 150-300ms, ease-out only
- Empty/loading states present
- Data numbers right-aligned with tabular-nums

**What this catches that Stages 1-5 miss:**
- Button renders but doesn't do anything (missing onClick handler)
- Data table renders but shows "undefined" (type mismatch at runtime)
- Layout breaks on tablet (CSS not responsive)
- Page crashes on load (runtime error not caught by TypeScript)
- Supabase query fails with RLS error (policy correct in SQL but wrong at runtime)
- Design system violation (wrong colors, wrong fonts, wrong spacing)

**For `/qa quick`:** Skip Stage 6 (too slow for quick checks)
**For `/qa fix`:** Stage 6 runs WITH auto-fix enabled (agent fixes what it finds)
**For `/qa visual`:** Force Layer 3 screenshots on every page (old behavior)

## Output Format

```
=========================================
QA REPORT — Redoe OS
=========================================

Stage 0: Naming Lint          [PASS/FAIL]
Stage 1: Schema Guardian      [PASS/FAIL]
Stage 2: Security Scan        [PASS/FAIL]
Stage 3: RLS Audit            [PASS/FAIL]
Stage 4: Code Review          [X issues]
Stage 5: Test Coverage        [X gaps]
Stage 6: Browser Verify       [PASS/FAIL/SKIP]
  L1+L2 DOM Audit:            X/Y checks passed
  L1.5 Interaction Audit:     Clicked X elements across Y pages, Z failures
  Expected Elements:          X/Y found [MISSING: list]
  L3 Screenshot:              [taken/skipped]

-----------------------------------------
RESULT: SAFE TO PUSH / DO NOT PUSH
-----------------------------------------

Issues Found:
1. [severity] [file:line] — [description]
2. ...

Click-Through Failures (if any):
1. [page] [element] — [what happened after click]
2. ...

Suggested Fixes:
1. [what to change and where]
2. ...
```

## Auto-Fix Mode (`/qa fix`)

When invoked with `fix`, after running the full pipeline:
1. Fix naming convention violations (`git mv` to rename files, update all imports/references)
2. Add missing `ENABLE ROW LEVEL SECURITY` statements
3. Add missing `created_at TIMESTAMPTZ DEFAULT NOW()` columns
4. Remove accidentally committed secrets (replace with env var references)
5. Generate missing pgTAP test files
6. Re-run the pipeline to verify fixes

Do NOT auto-fix:
- Breaking changes (DROP TABLE, DROP COLUMN) — require Steve's approval
- RLS policy logic — too business-critical for automation
- Design system violations in frontend — need human judgment

## When to Run

- **Before every merge to main.** This is the gate.
- **After writing a new migration.** Catches issues immediately.
- **After any code session.** Quick sanity check.
- **Weekly.** Full security audit (deeper than per-push check).

## Integration with GitHub Actions

When the monorepo has CI set up, this same pipeline runs automatically on PRs via `.github/workflows/db-qa.yml` and `.github/workflows/claude-review.yml`. The skills are the same — CI just triggers them without human intervention.

For now (Sprint 1), just run `/qa` locally before pushing. That's it.

## Review Readiness Dashboard (v8)

After pipeline completes, write results to `_workspace/review-status.json` in the scaffold directory:

```javascript
// Read existing file (or create empty object)
const status = JSON.parse(fs.readFileSync('_workspace/review-status.json')) || {};

// Update QA entry
status.qa = {
  completed: new Date().toISOString(),
  commit: getCurrentCommitShort(),  // git rev-parse --short HEAD
  health_score: computeHealthScore(),  // 0-100 based on stages passed
  result: allPassed ? "PASS" : "FAIL",
  stages: {
    schema: stage1Result,
    security: stage2Result,
    rls: stage3Result,
    code_review: stage4IssueCount,
    test_coverage: stage5GapCount,
    browser: stage6Result  // PASS/FAIL/SKIP
  }
};

fs.writeFileSync('_workspace/review-status.json', JSON.stringify(status, null, 2));
```

**Health Score Calculation:**
| Category | Weight | What it measures |
|----------|--------|-----------------|
| Schema | 15% | Migration naming, RLS presence, audit triggers |
| Security | 20% | No secrets, no service_role leaks |
| RLS | 20% | All tables have appropriate policies |
| Code Review | 15% | Must Fix count (0 = full score) |
| Test Coverage | 10% | pgTAP test gaps |
| Browser | 20% | Runtime verification (if applicable, else redistributed) |

Score < 60 = FAIL. Score 60-79 = WARN. Score 80+ = PASS.

This file is read by `/ship` to gate deployments. Don't delete it between runs — it accumulates state from all skills.
