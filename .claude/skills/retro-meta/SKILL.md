---
name: retro-meta
description: Analyze patterns across Claude Code session transcripts and corrections. Use when Steve says "meta review", "what patterns do you see", "how are we doing", invokes /retro-meta, or monthly as part of knowledge consolidation. Do NOT trigger on single-session retros (use /retro instead) or specific incident reviews.
---

Meta-analysis of Claude Code session patterns. Inspired by Thariq Shihipar's #1 metalearning: "Read your agent's transcripts over and over."

**Trigger:** `/retro-meta` command, or monthly alongside `/weekly` and `/knowledge-consolidation`.

## Step 1: Gather Session Data

Read the last 20 entries from `_System/session-log.md`. For each session, extract:
- Session number, date, duration
- What was attempted
- What succeeded / failed
- Any corrections Steve made
- Tools/skills/agents used

Also read:
- `_System/lessons.md` — recent additions (last 30 days)
- `memory/feedback_operating-principles.md` — current behavioral rules

## Step 2: Pattern Analysis

Analyze across sessions for:

**Repeated Corrections** — Same mistake appearing 2+ times despite being in lessons.md. This means the lesson isn't being enforced effectively. Consider: should it become a hook? A rules file entry? A skill gotcha?

**Deferral Frequency** — How often did the Stop hook catch incomplete work? What types of tasks get deferred most? Are certain skill categories more prone to deferral?

**Tool Usage Distribution** — Which skills/agents/hooks fire most? Which are never used? Candidates for consolidation or removal.

**Session Efficiency** — Average tasks completed per session. Sessions that hit compaction vs those that didn't. Correlation between session length and completion rate.

**Skill Misfires** — Cases where the wrong skill triggered. Update negative triggers.

**Context Rotation** — How often did sessions exceed 65%? Did HANDOFF.md accurately capture state for the next session?

## Step 3: Generate Meta-Review

Output format:
```markdown
## Meta Review ({date range})

### Patterns Found
1. {pattern} — seen in sessions {N, N, N}. Impact: {high/med/low}.
   **Action:** {specific change to make}

### Correction Audit
- {N} corrections in lessons.md last 30 days
- {N} are effectively enforced (hook/rule covers it)
- {N} are NOT enforced (need hook or rules file entry)
- List: {unenforced corrections}

### Skill Health
- Most used: {skill} ({N} invocations)
- Never used: {skills} — consider removing or merging
- Misfire candidates: {skills with wrong triggers}

### Efficiency Metrics
- Avg tasks/session: {N}
- Compaction rate: {N}% of sessions
- Stop hook rejection rate: {N}%

### Recommendations
1. {recommendation with specific file to change}
2. ...
```

## Step 4: Log & Act

1. Append findings summary to `data/reviews.jsonl`:
```json
{"date":"2026-03-21","sessions_reviewed":20,"patterns_found":3,"corrections_unenforced":2,"recommendations":["...","..."]}
```

2. For each recommendation with impact HIGH:
   - If it's a lessons.md → rules file promotion: do it now
   - If it's a hook change: propose it (Steve approves hooks)
   - If it's a skill description fix: do it now

3. Update `memory/feedback_operating-principles.md` if new behavioral patterns emerge

## Data Store

File: `.claude/skills/retro-meta/data/reviews.jsonl` (append-only)

Tracks review history so future runs can check: "Did we act on the last review's recommendations?"
