---
name: land-and-deploy
description: "Post-merge deploy verification for Redoe OS. After /ship creates a PR: merge it, wait for CI, wait for deploy, verify production health via /canary. Includes trust ladder — first deploys get dry-run + extra monitoring, trust builds over successful deploys. Closes the ship-to-production loop."
---

# /land-and-deploy — Merge, Deploy, Verify

`/ship` creates the PR. This skill lands it — merge, wait for CI, wait for deploy, verify production health. The missing link between "PR created" and "it's live and working."

**Team:** Steve (VP), Andy (backend), Ben Wang.

## Usage

```
/land-and-deploy              — Land the most recent PR from /ship
/land-and-deploy --pr 42      — Land a specific PR
/land-and-deploy --dry-run    — Run all checks without actually merging
/land-and-deploy --skip-canary — Merge + deploy but skip post-deploy monitoring
```

**When to run:**
- After `/ship` creates a PR and you're ready to merge
- Use `/ship --land` as shorthand (invokes `/ship` then `/land-and-deploy`)

---

## The Pipeline

### Phase 1: Pre-Merge Checks (30 seconds)

1. **CI status** — All checks must pass:
   ```bash
   gh pr checks [PR_NUMBER] --watch
   ```
   If any check fails: STOP. Report which check failed and why.

2. **Review status** — PR must be approved (or self-approved for solo work):
   ```bash
   gh pr view [PR_NUMBER] --json reviewDecision
   ```

3. **Merge conflicts** — Branch must be clean:
   ```bash
   gh pr view [PR_NUMBER] --json mergeable
   ```
   If conflicts: STOP. "Rebase required — run `git rebase main` on the feature branch."

4. **Trust ladder check** — How many successful deploys has this project had?
   Read `_workspace/deploy-history.json`:
   ```json
   {
     "successful_deploys": 12,
     "last_failure": null,
     "trust_level": "standard"
   }
   ```

### Phase 2: Merge (10 seconds)

```bash
gh pr merge [PR_NUMBER] --squash --delete-branch
```

- **Always squash merge** — one clean commit on main
- **Always delete branch** — clean up after ourselves
- Record merge commit SHA for tracking

### Phase 3: Wait for Deploy (1-3 minutes)

Monitor the deployment pipeline:

```bash
# Poll deploy status (Vercel example)
gh api repos/{owner}/{repo}/deployments --jq '.[0]'
```

**Wait states:**
- `pending` → keep polling (every 15 seconds)
- `in_progress` → keep polling
- `success` → proceed to Phase 4
- `failure` → ALERT. Report deploy failure. Do NOT proceed.
- `error` → ALERT. Report deploy error.

**Timeout:** If deploy hasn't completed in 10 minutes, WARN and ask for manual check.

### Phase 4: Production Verification

Invoke `/canary` with the production URL:

```
/canary --pages [affected-pages] --duration 3m
```

Pass affected pages from the PR:
```bash
gh pr view [PR_NUMBER] --json files -q '.files[].path' | grep 'apps/web/src/'
```

### Phase 5: Record Result

Update `_workspace/deploy-history.json`:

```json
{
  "deploys": [
    {
      "pr": 42,
      "merged_at": "2026-03-30T15:00:00Z",
      "deploy_status": "success",
      "canary_verdict": "HEALTHY",
      "commit": "abc1234",
      "version": "2026.03.3"
    }
  ],
  "successful_deploys": 13,
  "consecutive_successes": 8,
  "last_failure": null,
  "trust_level": "standard"
}
```

---

## Trust Ladder

Trust builds with each successful deploy. More trust = less friction.

| Level | After | What changes |
|-------|-------|-------------|
| **New** | 0 deploys | Dry-run first. 5-minute canary. Extra page checks. |
| **Cautious** | 3 successful deploys | Normal canary (3 min). All affected pages. |
| **Standard** | 8 successful deploys | Normal canary. Only key pages unless broad changes. |
| **Trusted** | 20 successful deploys | Quick canary (1 min). Health check + console only. |

**Trust resets to Cautious after any:**
- Deploy failure
- Canary finding (HIGH or CRITICAL)
- Production rollback
- Major version bump (schema migration, dependency upgrade)

---

## Output

### Success
```
=========================================
LAND AND DEPLOY — Redoe OS
=========================================
PR:            #42 — feat/SPEC-005-attendance-report
Merge:         ✓ Squash merged (abc1234)
Branch:        ✓ Deleted feat/SPEC-005-attendance-report
Deploy:        ✓ Live in 1m 42s
Canary:        ✓ HEALTHY (0 findings)

Trust level:   Standard (9 consecutive successes)
Version:       2026.03.3

Production is live and clean.
=========================================
```

### Failure
```
=========================================
LAND AND DEPLOY — Redoe OS
=========================================
PR:            #43 — fix/proxy-cors
Merge:         ✓ Squash merged (def5678)
Branch:        ✓ Deleted
Deploy:        ✓ Live in 2m 10s
Canary:        ✗ HIGH ALERT — 1 finding

Finding: TypeError on /jobs — "Cannot read properties of undefined"
Trust level:   Cautious → RESET (was Standard)

RECOMMENDATION: Investigate or revert.
  • /investigate "TypeError on /jobs after PR #43"
  • git revert def5678 && git push  (rollback)
=========================================
```

---

## Integration

- **`/ship`** — creates the PR. `/land-and-deploy` lands it.
  - `/ship --land` = `/ship` + `/land-and-deploy` in sequence
- **`/canary`** — invoked by Phase 4 for production verification
- **`/investigate`** — if canary finds issues, hand off to `/investigate`
- **`/retro`** — deploy history feeds into retro metrics (deploy frequency, failure rate)
- **`/careful`** — `/land-and-deploy` has elevated permissions during Phase 2 (can delete branches)

---

## What This Catches

- PRs that pass CI but break in production (environment differences)
- Deploys that silently fail (no error, but app doesn't update)
- Performance regressions that only appear under production load
- The "it works on my machine" gap between merge and production
- Trust decay after failures — forces extra caution when things have broken recently
