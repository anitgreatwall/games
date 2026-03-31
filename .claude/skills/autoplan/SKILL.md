---
name: autoplan
description: "One-command planning pipeline for Small Batch Redoe OS features. Chains /spec → /review-plan (lite) → /decompose automatically, surfacing only key decisions for approval. For Small Batch only — Big Batch still gets the full manual pipeline. Invoked via /autoplan or /autoplan [topic]."
---

# /autoplan — Fast-Track Planning for Small Batch

One command. Runs the full planning pipeline automatically. Only stops to ask you the decisions that matter — everything else runs on autopilot.

**For Small Batch features ONLY** (1-2 day appetite, <=3 tables). Big Batch features (1-2 week appetite, 4+ tables) must use the full manual pipeline: `/spec` → `/review-plan` → `/decompose`.

**Team:** Steve (VP, approves decisions), Andy (backend), Ben Wang.

## Usage

```
/autoplan                      — Start planning (ask what to build)
/autoplan "job list filtering"  — Start with topic pre-loaded
```

---

## The Pipeline

### Phase 0: Solutions Search (30 seconds)

Before asking any questions, search the Solutions Library:
1. Read `_Projects/Redoe-OS/docs/solutions/index.md`
2. Scan for tags matching the topic
3. If relevant solutions found: "We've solved something similar — SOLN-NNN. Key gotcha: [X]."
4. Factor findings into the spec questions below

### Phase 1: Quick Spec (5 minutes)

Run `/spec` in compressed mode:

1. **Q1: Who?** Present tier options. Wait for answer.
2. **Q2: What today?** "What are they doing now to solve this?"
3. **Q3: JTBD** "When ___, I want ___, so I can ___"
4. **Q4: Success** "What does done look like?" Push back if vague.
5. **Q5: Not** "What does this NOT do?" Get 3 exclusions.
6. **Appetite check:** Auto-classify as Small Batch. If it smells like Big Batch (4+ tables, complex state, multi-tier): **STOP and say so.** "This looks like Big Batch. Run `/spec` manually for the full 10-question interview."
7. **Quick edge cases:** Propose 2-3 from the standard list. Ask: "Any of these matter?"
8. **Lock it.** Generate the spec file. No adversarial review loop (that's for Big Batch).

<GATE name="spec-complete">
STOP. Verify the SPEC-NNN file was written to `_Projects/Redoe-OS/_specs/` and contains answers to all 5 questions + edge cases. If the file is missing or incomplete: DO NOT proceed to Phase 2. Go back and complete the spec.
</GATE>

### Phase 2: Lite Review (3 minutes)

Run `/review-plan` with Phase 1 (CEO) and Phase 2 (Eng) only. Skip Phase 3 (Design Preview) and Phase 4 (Cross-Model).

**CEO lite:**
- Reuse check: Search codebase for existing similar components/functions
- If overlap found: "Found [X] in [file] — extend instead of building new?"
- If not: proceed

**Eng lite:**
- One diagram (data flow or sequence — whichever is more useful)
- File count check: if >4 files, warn
- Quick performance check: "Any queries on large tables?"

**No alternatives step.** For Small Batch, the straightforward approach is usually correct. Don't over-engineer the planning.

<GATE name="review-complete">
STOP. Verify the review identified no Big Batch signals (4+ tables, complex state, multi-tier). If Big Batch signals found: STOP autoplan and redirect to full `/spec` + `/review-plan` pipeline.
</GATE>

### Phase 3: Auto-Decompose (2 minutes)

Run `/decompose` automatically:
- Small Batch = 2-3 tasks max
- Standard split: DB task + UI task (or DB + API + UI if Edge Function needed)
- Generate DECOMP file with branches, scopes, and merge order
- Show the decomp to Steve for approval

---

## Decision Points (Where It Stops)

Autoplan runs automatically EXCEPT at these checkpoints:

| Checkpoint | What it asks | Why it stops |
|-----------|-------------|-------------|
| After Q1-Q5 | "Here's what I heard. Anything wrong?" | Confirm understanding |
| If Big Batch detected | "This is too big for autoplan. Use /spec." | Prevent scope mismatch |
| If overlap found | "Found existing [X]. Extend it?" | Reuse > rebuild |
| After decomp | "Here's the task split. Good to go?" | Final approval before agents start |

Between checkpoints, it runs without asking.

---

## Output

Two files, generated automatically:

1. **Spec:** `_Projects/Redoe-OS/_specs/SPEC-NNN-slug.md` (compressed format — no pre-mortem, no risk assessment, no rabbit holes)
2. **Decomp:** `_Projects/Redoe-OS/_specs/DECOMP-NNN-slug.md` (2-3 tasks with branches and scopes)

Plus: Update `_workspace/review-status.json` with spec + review_plan entries.

<GATE name="decompose-complete">
STOP. Verify the DECOMP-NNN file exists, contains 2-3 tasks with branches and file scopes, and Steve has approved the task split. If missing or unapproved: DO NOT start building.
</GATE>

---

## When NOT to Use Autoplan

- Feature touches 4+ database tables → use `/spec` manually
- Feature requires new RLS policies → use `/spec` + `/review-plan` (security review needed)
- Feature affects Shop Floor AND Management tiers → use full pipeline (tier mismatch risk)
- Steve wants to think deeply about the problem → use `/spec` (the 10 questions are the value)
- Architectural decision involved → use `/review-plan` with alternatives step

**Rule of thumb:** If you'd regret skipping the full interview, don't use autoplan.

---

## Integration

- **`/spec`** — autoplan calls this in compressed mode
- **`/review-plan`** — autoplan calls phases 1-2 only
- **`/decompose`** — autoplan calls this automatically
- **`/qa`** → **`/ship`** — after autoplan, the normal pipeline continues

**The sprint:**
```
/autoplan → agents build → /qa → /design-review → /ship → /canary → /retro
```

---

## What This Saves

Full pipeline for a Small Batch feature:
- `/spec` (10 questions): ~15 minutes
- `/review-plan` (4 phases): ~15 minutes
- `/decompose`: ~5 minutes
- Total: ~35 minutes

Autoplan for the same feature:
- Compressed spec (5 questions): ~5 minutes
- Lite review (2 phases): ~3 minutes
- Auto-decompose: ~2 minutes
- Total: ~10 minutes

**25 minutes saved per Small Batch feature.** At 2-3 Small Batch features per week, that's 1+ hour/week of planning overhead eliminated.
