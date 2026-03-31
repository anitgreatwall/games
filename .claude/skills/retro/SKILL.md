---
name: retro
description: Structured retrospective that captures what worked and what didn't, then FEEDS FINDINGS BACK INTO SKILL UPDATES. The learning loop. Use after every Big Batch feature ships, after any production incident, after any session where something went wrong, or weekly. Invoked via /retro or /retro [feature-name].
---

# /retro — Learn and Update

Structured retrospective with one rule: every retro must result in at least ONE skill or config update. Learning without action is noise.

**Team:** Steve (VP), Andy (backend), Ben Wang.

## Usage

```
/retro                     — Start a retro (ask what it's about)
/retro [feature-name]      — Retro on a specific feature or incident
/retro weekly              — Weekly process retro (not tied to a feature)
```

**When to run:**
- After every Big Batch feature ships
- After any production incident
- After any session where something went wrong
- Weekly (optional — covers the week's work collectively)

---

## Before Starting

1. If retro is about a specific spec: read `_Projects/Redoe-OS/_specs/SPEC-NNN-slug.md`
2. If a DECOMP exists: read `_Projects/Redoe-OS/_specs/DECOMP-NNN-slug.md`
3. Read recent git log for the relevant branch/feature
4. Read `_System/lessons.md` to avoid re-learning known lessons
5. Check for prior retros in `_Projects/Redoe-OS/_workspace/` to spot recurring themes

---

## Ask These 5 Questions (one at a time)

Keep it conversational. Steve is not filling out a form — he's reflecting. Push for specifics. "The spec was bad" is not useful. "The spec didn't cover offline mode and we lost 2 hours" is useful.

**Q1: What went well?**
What should we keep doing? What was faster or better than expected?
- Prompt if stuck: "What would you do exactly the same way next time?"
- Look for: skills that worked, patterns worth repeating, agent behaviors to preserve

**Q2: What went wrong?**
What broke? What took longer than expected? What was frustrating?
- Prompt if stuck: "Where did you feel like you were fighting the tools instead of building?"
- Look for: missing checks, bad assumptions, skill gaps, communication failures

**Q3: What surprised us?**
Unexpected issues, edge cases, discoveries — good or bad.
- Prompt if stuck: "What did you learn that you didn't know before starting?"
- Look for: undocumented system behaviors, user needs we missed, technical gotchas

**Q4: What should we change?**
Specific, actionable changes to process, skills, or pipeline.
- Push back on vague answers: "Change the process" → "Which step? What specifically?"
- Each change must be: [What] + [Where] + [Why]

**Q5: What did we learn?**
New patterns, domain knowledge, risk factors for next time.
- Prompt if stuck: "If you were briefing someone starting a similar project tomorrow, what would you warn them about?"

---

## After the 5 Questions — The Feedback Loop

This is the step that makes retros valuable. Without it, retros are theater.

### Step 1: Write the Retro Summary

Write to `_Projects/Redoe-OS/_workspace/retro-YYYY-MM-DD.md` (or `retro-YYYY-MM-DD-feature-name.md` if feature-specific).

Use this format:

```markdown
# Retro: [Feature/Sprint Name] — YYYY-MM-DD

## What Went Well
- ...

## What Went Wrong
- ...

## What Surprised Us
- ...

## Changes Made
- Updated `/spec` edge cases: added [X]
- Updated `/qa` Stage 6: now checks for [Y]
- Added to `_System/lessons.md`: [Z]

## Open Questions
- ...
```

### Step 2: Feed Back Into Skills (MANDATORY)

For EACH actionable finding from Q2-Q5, apply the change NOW. Not "we should update." UPDATE.

| Finding Type | Where to Update |
|---|---|
| /spec didn't ask about [X] | `.claude/skills/spec/SKILL.md` — add to edge case list or question prompts |
| /spec-review missed [X] | `.claude/skills/spec/references/review-checklist.md` — add checklist item |
| /review-plan didn't catch [X] | `.claude/skills/review-plan/SKILL.md` — add to relevant phase |
| /decompose split was wrong | `.claude/skills/decompose/SKILL.md` — add splitting rule |
| /qa missed a bug type | `.claude/skills/qa/SKILL.md` — add to relevant stage |
| Agent did something dumb | `AGENTS.md` or relevant agent config — add constraint |
| Domain fact discovered | `_System/lessons.md` — add under appropriate section |
| Redoe-specific edge case | `.claude/skills/spec/SKILL.md` — add to Redoe edge case list |
| Design system gap | Design system reference file — add the missing pattern |
| Process step missing | Relevant skill or `_System/execution-protocol.md` |

### Step 3: Write Solution Doc (MANDATORY)

Run `/solutions` to capture what was learned as a searchable solution doc. Every retro must produce at least one solution entry in `_Projects/Redoe-OS/docs/solutions/`.

Ask: "What did we solve that someone will hit again?" If nothing from this retro qualifies, state why explicitly — don't silently skip.

### Step 4: Summarize What Changed

After making updates, list every file modified and what was added. This is the retro's receipt — proof that learning happened.

```
Files updated:
- .claude/skills/spec/SKILL.md — added "offline mode" to edge case list
- .claude/skills/qa/SKILL.md — Stage 6 now checks for stale cache on page reload
- _System/lessons.md — added: "Supabase RLS policies don't apply to service_role"
```

---

## Recurring Theme Detection

When writing a retro, scan previous retros in `_workspace/retro-*.md`. If the SAME issue appears in 2+ retros:

1. Flag it: "This is the 3rd time [X] has come up."
2. Escalate the fix — a skill update wasn't enough. Consider:
   - Adding a hook (`.claude/settings.json`) to enforce it automatically
   - Adding a pre-commit check
   - Restructuring a skill's flow so the issue can't happen
3. Log the pattern in `_System/lessons.md` with a "recurring" tag

---

## The Rule

Every retro must result in **at least ONE** skill or config update. If the retro doesn't change anything, it wasn't useful — push harder on Q4 and Q5 until something actionable emerges.

---

## Persistent Metrics (v8)

After the 5 questions and feedback loop, collect and persist quantitative metrics for week-over-week trending.

### Step 5: Collect Metrics

Gather these data points automatically from git and the project:

```bash
# Commits this period
git log --oneline --since="$PERIOD_START" --until="$PERIOD_END" | wc -l

# Lines changed
git diff --stat $(git log --since="$PERIOD_START" --format="%H" | tail -1)...HEAD

# Test ratio (lines of test code / lines of app code)
find supabase/tests apps/web/src -name "*.test.*" -o -name "*.spec.*" | xargs wc -l
find apps/web/src -name "*.tsx" -o -name "*.ts" ! -name "*.test.*" ! -name "*.spec.*" | xargs wc -l

# Commit type breakdown
git log --oneline --since="$PERIOD_START" | grep -c "^.*feat:"    # features
git log --oneline --since="$PERIOD_START" | grep -c "^.*fix:"     # fixes
git log --oneline --since="$PERIOD_START" | grep -c "^.*db:"      # migrations

# Hotspot files (most changed)
git log --since="$PERIOD_START" --name-only --format="" | sort | uniq -c | sort -rn | head -10

# Skill usage (from review-status.json history if available)
```

### Step 6: Persist Metrics Snapshot

Save to `_workspace/retro-history/retro-YYYY-MM-DD.json`:

```json
{
  "date": "2026-03-23",
  "period": "2026-03-17 to 2026-03-23",
  "feature_or_sprint": "SPEC-012 time-tracking",
  "metrics": {
    "commits": 47,
    "lines_added": 2340,
    "lines_removed": 890,
    "test_lines": 680,
    "test_ratio": 0.29,
    "feat_commits": 12,
    "fix_commits": 8,
    "db_commits": 5,
    "fix_ratio": 0.17,
    "hotspot_files": ["src/app/page.tsx", "supabase/migrations/001.sql"],
    "qa_health_score": 92,
    "specs_completed": 1,
    "review_plans_completed": 1
  },
  "findings": {
    "went_well": ["..."],
    "went_wrong": ["..."],
    "changes_made": ["file1: added X", "file2: updated Y"]
  }
}
```

### Step 7: Week-over-Week Comparison

If previous retro snapshots exist in `_workspace/retro-history/`, compare:

```
Metrics Trend (vs last retro)
==============================
Commits:      47 (+12, ↑34%)
Test ratio:   29% (+5%, ↑ GOOD)
Fix ratio:    17% (-3%, ↓ GOOD — fewer bugs)
Health score: 92 (+4, ↑)
Hotspot:      page.tsx (3rd retro in a row — consider splitting)
==============================
```

**Alerts:**
- Fix ratio > 30%: "More than 30% of commits are fixes. Are we introducing bugs faster than features?"
- Test ratio < 20%: "Test coverage declining. Run /test-gen on new code."
- Same hotspot file 3+ retros: "This file keeps changing. Consider refactoring or splitting."
- Health score declining 2+ retros: "Quality trending down. Review recent /qa results."

### Step 8: Shipping Streak

Track consecutive days/weeks with at least one feature shipped:
```
Shipping Streak: 4 weeks 🔥
Last break: 2026-02-23 (blocked on SAP integration)
```

Persist streak count in the retro snapshot. If streak breaks, note why.

---

## Integration

- **`/spec`** → **`/review-plan`** → **`/decompose`** → build → **`/qa`** → **`/ship`** → **`/retro`** (this skill)
- /retro feeds improvements back into /spec, /review-plan, /decompose, /qa — closing the loop
- Persistent metrics enable trend analysis across retros — the compounding engine gets data-driven
- **`/solutions`** — called by Step 3 to capture learnings as searchable solution docs
- Over time, retros make every other skill better. This is the compounding engine.
