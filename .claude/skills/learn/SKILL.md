---
name: learn
description: "Cross-session learning system with confidence decay. Manages project learnings — patterns, corrections, preferences — with confidence scores (1-10). Inferred patterns decay over time; user-confirmed preferences never decay. Prevents lesson bloat. Use /learn to review, search, prune, or add learnings."
---

# /learn — Self-Maintaining Project Memory

Manages what the project has learned across sessions. Every learning has a confidence score. Stale patterns fade. Confirmed preferences stick.

**Team:** Steve (VP), Andy (backend), Ben Wang. The system learns from corrections and compounds knowledge — but unlike a growing text file, it prunes itself.

## Usage

```
/learn                    — Show active learnings (confidence ≥ 5)
/learn add "..."          — Add a new learning (prompts for category + confidence)
/learn search [query]     — Search learnings by keyword
/learn review             — Interactive review: confirm, adjust, or prune each learning
/learn prune              — Remove all learnings below confidence threshold (default: 3)
/learn export             — Export learnings as markdown (for sharing or backup)
/learn stats              — Show learning counts by category, avg confidence, decay candidates
```

---

## Learning Schema

Each learning is stored as a JSON line in `_workspace/learnings.jsonl`:

```json
{
  "id": "learn-001",
  "created": "2026-03-30T14:00:00Z",
  "updated": "2026-03-30T14:00:00Z",
  "category": "pattern",
  "source": "user-confirmed",
  "confidence": 8,
  "content": "Shop floor pages must use single-column layout with 56px touch targets",
  "context": "Steve corrected a two-column layout on the time clock page — operators wearing gloves couldn't hit buttons",
  "tags": ["shop-floor", "layout", "accessibility"]
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Auto-generated: `learn-NNN` |
| `created` | ISO datetime | When the learning was first recorded |
| `updated` | ISO datetime | Last time confidence was refreshed |
| `category` | enum | `pattern`, `correction`, `preference`, `architecture`, `domain`, `tooling` |
| `source` | enum | `user-confirmed` (Steve said it), `inferred` (observed from code/behavior), `retro` (from /retro) |
| `confidence` | 1-10 | How certain we are this still applies |
| `content` | string | The learning itself — one clear sentence |
| `context` | string | Why this was learned — the incident or correction that prompted it |
| `tags` | string[] | For search/filtering |

---

## Confidence System

### Scoring

| Score | Meaning | Example |
|-------|---------|---------|
| 10 | Absolute rule, never changes | "Every table must have RLS enabled" |
| 8-9 | Strong pattern, confirmed multiple times | "Shop floor = single column, 56px buttons" |
| 6-7 | Observed pattern, seems reliable | "Steve prefers bundled PRs over many small ones" |
| 4-5 | Inferred, not yet confirmed | "This API endpoint seems to timeout after 30s" |
| 1-3 | Stale or uncertain | Candidates for pruning |

### Decay Rules

| Source | Decay rate | Rationale |
|--------|-----------|-----------|
| `user-confirmed` with confidence ≥ 8 | **No decay** | Steve said it explicitly — it's a rule until he says otherwise |
| `user-confirmed` with confidence < 8 | -1 per 60 days | Preferences can change |
| `inferred` | -1 per 30 days | Patterns observed from code need reconfirmation |
| `retro` | -1 per 45 days | Retro findings are specific to a moment in time |

### Refresh

A learning's confidence is refreshed (decay timer resets) when:
- Steve confirms it again ("yes, that's still the rule")
- The pattern is observed again in code (for `inferred` type)
- `/learn review` — user marks it as still valid
- Another skill references it and the referenced behavior succeeds

---

## How Learnings Get Created

### Automatic (from other skills)

| Skill | When | Category |
|-------|------|----------|
| `/retro` | After each retrospective | `retro` — what worked, what didn't |
| `/investigate` | After root cause found | `pattern` — the bug pattern to watch for |
| `/qa` | After repeated failures | `correction` — what keeps failing and why |
| `/code-review` | After recurring feedback | `pattern` — repeated review findings |
| `/spec` | After spec revisions | `preference` — what Steve wants in specs |

### Manual

```
/learn add "Never use Calibri font — always Arial for all documents"
```
Prompts for:
- Category: `preference`
- Confidence: (default 8 for user-confirmed)
- Tags: `formatting`, `documents`

---

## Integration with Existing Systems

### Relationship to `_System/lessons.md`

`_System/lessons.md` is the current system. `/learn` augments it:

| Aspect | lessons.md | /learn |
|--------|-----------|--------|
| Format | Freeform markdown | Structured JSONL |
| Decay | None (grows forever) | Confidence-based decay |
| Search | Grep | Structured query |
| Source tracking | Manual | Automatic (which skill, when) |
| Pruning | Manual | `/learn prune` |

**Migration path:** Run `/learn import-lessons` to convert existing `_System/lessons.md` entries into structured learnings with initial confidence scores. Keep `lessons.md` as the human-readable view; `learnings.jsonl` is the machine-readable backend.

### Relationship to Memory Files

`memory/` files in the vault are cross-project (Steve's preferences, communication style, etc.). `/learn` is project-scoped (Redoe OS patterns, architecture decisions, team corrections).

- **memory/** = "Steve always wants Arial font" (applies everywhere)
- **learnings.jsonl** = "The jobs page RLS policy needs tier 2+ for cross-job visibility" (Redoe OS specific)

---

## Output

### `/learn` (show active)

```
=========================================
ACTIVE LEARNINGS — Redoe OS (17 active, 3 decayed)
=========================================

Patterns (8):
  [10] Every table must have RLS enabled — confirmed by security audit
  [ 9] Shop floor pages: single-column, 56px buttons, no sidebar
  [ 8] Time clock page is highest-traffic — test first after any deploy
  [ 7] SAP sync can timeout after 30s — always handle with retry
  ...

Corrections (4):
  [ 9] Don't use service_role key in client code — caught in code review
  [ 8] DM Sans → Inter font switch (v11.0.0) — design system update
  ...

Preferences (3):
  [10] Bundled PRs preferred over many small ones for refactors
  [ 8] Steve wants dense data tables, not card-based layouts for management
  ...

Decay candidates (confidence ≤ 5):
  [ 4] Vercel build sometimes fails on first try — retry usually works
  [ 3] Ben prefers verbose commit messages — may have changed
=========================================
```

### `/learn stats`

```
Total: 20 learnings (17 active, 3 below threshold)
By category: pattern(8) correction(4) preference(3) architecture(2) domain(2) tooling(1)
By source: user-confirmed(12) inferred(5) retro(3)
Avg confidence: 7.2
Next decay check: 4 learnings will decay within 30 days
```

---

## Anti-Patterns

- Don't add learnings for things already in CLAUDE.md — those are canonical rules, not learnings
- Don't add learnings for one-time fixes — only patterns that recur
- Don't set confidence to 10 unless it's truly a permanent rule
- Don't skip context — "why" is as important as "what"
- Don't let learnings.jsonl exceed 100 entries — prune aggressively
