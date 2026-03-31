---
name: ship
description: "Full deployment pipeline for Redoe OS. Runs regression → version bump → changelog → PR creation. Zero-confirmation automation. Gates on Review Readiness Dashboard — won't ship without passing /spec, /review-plan, /qa, and /code-review. Invoked via /ship or /ship [branch-name]."
---

# /ship — Merge, Test, Version, Deploy

One command. Runs the full pipeline from current branch to merged PR. No confirmation prompts — if it passes, it ships.

**Team:** Steve (VP), Andy (backend), Ben Wang. This must be copy-paste simple.

## Usage

```
/ship              — Ship current branch (auto-detect)
/ship [branch]     — Ship a specific branch
/ship --dry-run    — Run everything except PR creation (preview mode)
/ship --land       — Ship + merge PR + verify production deploy (v9)
```

## Pre-Flight Checks

Before anything else, verify we're ready to ship:

### 1. Branch Check
```bash
BRANCH=$(git branch --show-current)
```
- If on `main`: STOP. "You're on main. Switch to a feature branch first."
- If branch has no commits ahead of main: STOP. "Nothing to ship — branch is up to date with main."

### 2. Review Readiness Dashboard

Read `_workspace/review-status.json` in the Redoe OS scaffold directory. This file is written by other skills as they complete.

```json
{
  "spec": { "completed": "2026-03-23T14:00:00Z", "commit": "abc1234", "id": "SPEC-NNN" },
  "review_plan": { "completed": "2026-03-23T15:00:00Z", "commit": "abc1234" },
  "qa": { "completed": "2026-03-23T16:00:00Z", "commit": "def5678", "health_score": 92 },
  "code_review": { "completed": "2026-03-23T16:30:00Z", "commit": "def5678", "verdict": "APPROVE" }
}
```

**Check staleness:** Compare each review's `commit` against current HEAD.
```bash
CURRENT_HEAD=$(git rev-parse --short HEAD)
```
- If a review's commit doesn't match HEAD: mark as STALE
- If `review-status.json` doesn't exist: warn but don't block (file is new in v8)

**Gate rules:**
| Review | Required? | Action if missing/stale |
|--------|-----------|------------------------|
| spec | Required for Big Batch | WARN for Small Batch, BLOCK for Big Batch |
| review_plan | Required for Big Batch | WARN for Small Batch, BLOCK for Big Batch |
| qa | ALWAYS required | BLOCK — run `/qa` first |
| code_review | Recommended | WARN — "No code review on record. Proceed anyway?" |

Display the dashboard:
```
Review Readiness Dashboard
==========================
Spec:        PASS (SPEC-012, 2h ago)
Review Plan: PASS (2h ago)
QA:          PASS (score: 92, 1h ago)
Code Review: STALE (was abc1234, HEAD is def5678) ⚠
==========================
```

If BLOCKED: stop and tell the user which skill to run first.

### 3. Clean Working Tree
```bash
git status --porcelain
```
If dirty: STOP. "Uncommitted changes. Commit or stash first."

---

## Pipeline

### Stage 1: Merge Base Branch

Pull latest main and merge into feature branch. This ensures tests run against the latest code.

```bash
git fetch origin main
git merge origin/main --no-edit
```

If merge conflicts:
1. List conflicting files
2. STOP. "Merge conflicts with main. Resolve before shipping."
   - Show the conflicting files and first 10 lines of each conflict
   - Do NOT auto-resolve — human decision required

### Stage 2: Run Full Regression

Invoke the regression skill's full pipeline:
```
/regression full
```

This runs all 6 tracks: pgTAP, RLS audit, type freshness, lint, type-check, Vitest, Playwright E2E.

**Test Failure Triage:**
For each failure, classify:
- **In-branch failure** (introduced by this branch's changes): BLOCK. Fix required.
- **Pre-existing failure** (exists on main too): WARN. Log it but don't block ship.

To classify: check if the same test fails on main:
```bash
git stash
git checkout main
# run the failing test
git checkout -
git stash pop
```

If in-branch failures exist: STOP. List failures with file:line citations. Fix, commit, re-run `/ship`.

<GATE name="regression-passed">
STOP. Verify ALL regression tracks passed (or pre-existing failures only). If any in-branch failure exists: DO NOT proceed. Fix the failure and re-run `/ship`.
</GATE>

### Stage 3: Adversarial Review (auto-scaled by diff size)

Count changed lines:
```bash
DIFF_SIZE=$(git diff --stat main...HEAD | tail -1 | grep -oP '\d+ insertion' | grep -oP '\d+')
```

| Diff size | Review level |
|-----------|-------------|
| < 50 lines | SKIP — too small to justify |
| 50-199 lines | Quick scan: check for security issues, RLS gaps, naming violations |
| 200+ lines | Full review: spawn a code-review subagent with the full diff |

For 200+ line diffs, the review subagent checks:
1. Security: secrets, service_role, SQL injection
2. RLS: new tables have policies, financial data restricted
3. Design system: correct tokens, shop floor rules
4. Performance: N+1 queries, missing indexes, SELECT *

If "Must Fix" issues found: STOP. List issues. Fix, commit, re-run `/ship`.

### Stage 4: Version Bump + Changelog

**Versioning:** CalVer format `YYYY.MM.patch` (already in CLAUDE.md).

1. Read current version from `package.json` (or `VERSION` file if exists)
2. Determine bump:
   - Same month as last release: increment patch (`2026.03.1` → `2026.03.2`)
   - New month: reset patch (`2026.03.5` → `2026.04.0`)
3. Update version in `package.json`
4. Generate changelog entry from commits:

```bash
git log --oneline main...HEAD
```

Write to `CHANGELOG.md` (prepend, don't append):
```markdown
## [YYYY.MM.patch] — YYYY-MM-DD

### Added
- [feature descriptions from feat: commits]

### Changed
- [change descriptions from chore:/refactor: commits]

### Fixed
- [fix descriptions from fix: commits]

### Database
- [migration descriptions from db: commits]
```

Commit the version bump + changelog:
```bash
git add package.json CHANGELOG.md
git commit -m "release: vYYYY.MM.patch"
```

### Stage 5: Push + Create PR

```bash
git push -u origin $BRANCH
```

Create PR with auto-generated body:

```bash
gh pr create --title "$PR_TITLE" --body "$(cat <<'EOF'
## Summary
<!-- Auto-generated from commits -->

## Review Status
- Spec: [status]
- Review Plan: [status]
- QA: [status] (health score: X)
- Code Review: [status]

## Regression Results
| Track | Status |
|-------|--------|
| pgTAP | PASS/FAIL |
| RLS Audit | PASS/FAIL |
| Type Freshness | PASS/FAIL |
| Lint | PASS/FAIL |
| TypeScript | PASS/FAIL |
| Vitest | PASS/FAIL |
| Playwright | PASS/FAIL |

## Changelog
<!-- Copy from CHANGELOG.md entry -->

---
🤖 Shipped with `/ship` v8 — Redoe OS Quality Pipeline
EOF
)"
```

PR title format: `[SPEC-NNN] Short description` (if spec exists) or conventional commit style.

<GATE name="pr-created">
STOP. Verify the PR was created successfully and the URL is valid. If PR creation failed (auth error, branch conflict, CI block): DO NOT proceed to post-ship. Fix the issue and retry Stage 5.
</GATE>

### Stage 6: Post-Ship

1. Update `_workspace/review-status.json` — reset all fields (new cycle)
2. Print the PR URL
3. Summary:

```
=========================================
SHIPPED — Redoe OS vYYYY.MM.patch
=========================================
Branch:     feat/SPEC-NNN-slug
PR:         #123 (https://github.com/...)
Version:    YYYY.MM.patch
Tests:      X/X passed
Review:     All gates passed
Changelog:  Updated
=========================================

Next: merge the PR on GitHub, then run /retro
```

---

## Stage 7: Land & Verify (`/ship --land` only) (v9)

When `--land` is specified, continue after PR creation:

### 7a. Merge the PR
```bash
gh pr merge $PR_NUMBER --squash --delete-branch
```

If merge fails (CI not passing, conflicts):
- Report the failure reason
- STOP — do not force merge

### 7b. Wait for Deploy
Poll the deployment status (Vercel):
```bash
# Check latest deployment status
gh api repos/{owner}/{repo}/deployments --jq '.[0]'
```

Wait until deployment status is "success" (poll every 15 seconds, timeout after 5 minutes).

If deploy fails: **ALERT — "Deploy failed after merge. Check Vercel dashboard."**

### 7c. Run Canary
Invoke `/canary` on the production URL:
- Check all affected pages for console errors
- Verify key pages load
- Compare performance against baseline
- Report healthy or alert

### 7d. Doc Drift Check
After successful deploy, scan for stale documentation:
```bash
# Check if CHANGELOG.md mentions the new version
# Check if README.md references match current features
# Check if scaffold CLAUDE.md is up to date
```

For each stale doc found: note in the post-ship report (advisory, not blocking).

### 7e. Post-Land Summary
```
=========================================
LANDED — Redoe OS vYYYY.MM.patch
=========================================
PR:         #123 merged (squash)
Deploy:     SUCCESS (Vercel)
Canary:     HEALTHY (0 errors, 0 regressions)
Doc Drift:  1 stale reference (CHANGELOG.md)
=========================================

Next: run /retro
```

---

## Dry Run Mode (`/ship --dry-run`)

Runs stages 1-4 (merge, test, review, version) but skips Stage 5 (push + PR) and Stage 6 (post-ship). Shows what WOULD happen:

```
DRY RUN — No PR created
Would ship: vYYYY.MM.patch
Would create PR: "[SPEC-NNN] Feature name"
X tests passed, Y issues found
```

---

## Integration

- **`/spec`** → **`/review-plan`** → **`/decompose`** → build → **`/qa`** → **`/ship`** (this skill) → **`/retro`**
- `/ship` reads from the Review Readiness Dashboard that other skills write to
- `/ship` is the ONLY way code gets to a PR. No manual `gh pr create`.
- After `/ship`, always run `/retro` to close the learning loop

---

## What This Catches

- Shipping without a spec (Big Batch gate)
- Shipping with stale reviews (commit mismatch)
- Shipping with merge conflicts (pre-merge check)
- Shipping with failing tests (full regression)
- Shipping with security issues (adversarial review on 200+ line diffs)
- Shipping without version tracking (CalVer enforcement)
- Shipping without changelog (auto-generated)
