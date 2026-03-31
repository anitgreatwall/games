---
name: investigate
description: "Systematic root-cause debugging for Redoe OS. Iron Law: no fixes without investigation. Traces data flow, tests hypotheses, stops after 3 failed fixes and questions architecture. Auto-freezes edits to the affected module. Use when something breaks, /qa Stage 6 finds a bug, or agents are thrashing on a fix."
---

# /investigate — Find the Root Cause, Then Fix

When something breaks, follow this process instead of randomly trying fixes. The Iron Law: **no fixes without investigation first.**

**Team:** Steve (VP), Andy (backend), Ben Wang. When Steve says "it's broken" — this is the skill to run.

## Usage

```
/investigate                       — Start investigation (describe the bug)
/investigate "jobs page crashes"   — Start with bug description
```

---

## The Process

### Step 1: Reproduce
Can we make it fail consistently?

- Get the exact error message, stack trace, or behavior description
- Identify: which page, which user action, which data state triggers it
- If intermittent: what conditions make it happen? (specific user, specific data, time-based?)
- Attempt to reproduce in dev environment

**If we can't reproduce:** Ask Steve for more details. "What did you click? What data was on screen? What time?" Don't guess — get facts.

### Step 2: Isolate
Where is the failure?

| Layer | How to check |
|-------|-------------|
| Frontend (React) | Browser console errors, component render trace |
| API (Edge Function) | Supabase Edge Function logs, request/response inspection |
| Database (RLS/query) | Supabase dashboard → SQL editor, check RLS policies |
| Auth | Check JWT claims, tier assignment, auth.uid() |
| Infrastructure | Supabase status page, Vercel deploy status |
| External (SAP, Lark) | Check sync_state table, adapter logs |

**Quick triage questions:**
- Does it fail for all users or just one tier?
- Does it fail with all data or specific records?
- Did it work before? If yes, what changed? (`git log --oneline -10`)
- Is it a build error, runtime error, or data error?

### Step 3: Freeze Scope

**AUTO-FREEZE:** Once the affected module is identified, restrict edits to that directory only.

```
FREEZE SCOPE: apps/web/src/components/job-table/
```

This prevents "while I'm here, let me also fix..." drift. Only files in the frozen scope can be edited until the investigation closes.

If the bug spans multiple modules, freeze to the narrowest common parent.

### Step 4: Hypothesize
List 3-5 possible root causes, ranked by likelihood.

```markdown
## Hypotheses

1. [LIKELY] RLS policy blocks Shop Floor from reading job costs → 403 on job detail page
   Evidence needed: Check RLS policies for jobs table, test with Shop Floor JWT

2. [POSSIBLE] Missing null check on customer_name → crashes when job has no customer
   Evidence needed: Check for jobs with null customer_id in seed data

3. [UNLIKELY] Stale TypeScript types after migration → runtime field mismatch
   Evidence needed: Compare database.types.ts against current schema
```

For each hypothesis: what evidence would CONFIRM it? What would ELIMINATE it?

### Step 5: Test Hypotheses (One at a Time)

Start with the most likely cause.

1. Add a targeted debug statement (console.log, SQL EXPLAIN, network inspection)
2. Run the reproduction steps
3. Check the evidence:
   - **Confirmed** → proceed to Step 6 (Fix)
   - **Eliminated** → move to next hypothesis
   - **Inconclusive** → refine the test, get more specific

**THE 3-STRIKE RULE:**
After 3 failed fix attempts on the same bug:
1. **STOP fixing.**
2. Write down what you've tried and why each failed.
3. Question the architecture: "Is the bug a symptom of a deeper design problem?"
4. Escalate: present findings to Steve with a recommendation.

```
INVESTIGATION STALLED after 3 attempts:
- Attempt 1: Fixed null check → still crashes (not the null)
- Attempt 2: Updated RLS policy → different error now (closer but not it)
- Attempt 3: Regenerated types → no change (types were fine)

ROOT CAUSE THEORY: The job detail page assumes data is loaded synchronously,
but Supabase returns data asynchronously after RLS evaluation. The component
renders before data arrives. This is an architectural issue, not a point fix.

RECOMMENDATION: Wrap job detail in a Suspense boundary with loading skeleton.
This is a 30-minute fix but touches the page architecture.
```

### Step 6: Fix (After Confirmed Root Cause)

1. **Write a test that reproduces the bug FIRST**
   - pgTAP test if database issue
   - Vitest test if component issue
   - Run it — confirm it FAILS (red)

2. **Apply the minimum fix**
   - Fix the root cause, not the symptom
   - Don't refactor unrelated code
   - Don't "improve" things while you're here

3. **Run the test — confirm it PASSES (green)**

4. **Check for siblings:** Does the same bug pattern exist elsewhere?
   ```bash
   grep -r "the pattern that caused the bug" apps/web/src/
   ```
   If found: fix those too (same test-first approach)

5. **Commit with context:**
   ```
   fix(jobs): handle async data load in job detail page

   Root cause: component rendered before Supabase RLS evaluation completed.
   Added Suspense boundary with loading skeleton.

   Reproduces: navigate to /jobs/G-2547 as Shop Floor user
   Test: tests/job-detail-loading.test.ts
   ```

### Step 7: Document

- If it's a pattern we should avoid → update `_System/lessons.md`
- If the edge case wasn't in the spec → update the spec's Edge Cases section
- If it reveals a missing check → update the relevant skill (/qa, /code-review, /schema-guardian)
- Remove the freeze scope

---

## Anti-Patterns

| Don't | Do Instead |
|-------|-----------|
| Randomly change code hoping it fixes the bug | Follow the hypothesis → test → confirm flow |
| Fix the symptom without understanding the cause | Find the root cause first |
| Skip the reproduction step ("I think I know what it is") | Always reproduce first |
| Fix 5 things at once in one commit | One fix per commit, with the test |
| Keep trying after 3 failed attempts | Stop, write up findings, escalate |
| Edit files outside the frozen scope | Stay in scope; if the fix is elsewhere, update the freeze |
| Say "it works now" without a regression test | Write the test. Always. |

---

## Integration

- **`/qa` Stage 6** — when browser verification finds a bug it can't fix in 2 attempts, invoke `/investigate`
- **`/freeze` scope** — auto-activated by this skill, prevents drift
- **`/retro`** — after investigation closes, run a mini-retro: "What should we add to /qa or /spec to catch this earlier?"
- **`_System/lessons.md`** — update with any new domain knowledge discovered

---

## Output Format

```
=========================================
INVESTIGATION REPORT
=========================================
Bug:        Jobs page crashes for Shop Floor users
Reproduced: YES — navigate to /jobs as tier 1 user
Root Cause: RLS policy on job_costs returns 0 rows for Shop Floor,
            but component assumes non-empty array
Fix:        Added empty state handler + conditional cost column visibility
Test:       tests/job-list-shop-floor.test.ts (was RED, now GREEN)
Siblings:   Checked 4 similar list pages — no same pattern found
Scope:      apps/web/src/components/job-table/ (FREEZE released)
Lesson:     Added to lessons.md: "Always handle empty RLS results"
=========================================
```
