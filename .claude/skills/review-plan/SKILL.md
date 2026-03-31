---
name: review-plan
description: "Challenge the approach before any code is written (v8). Four phases — CEO scope challenge, eng architecture review (with Error/Rescue Registry), design preview, and optional cross-model Outside Voice. Writes to Review Readiness Dashboard for /ship gating. Use after /spec is locked and before /decompose. Mandatory for Big Batch. Skip for Small Batch unless 3+ tables. Invoked via /review-plan or /review-plan SPEC-NNN."
---

# /review-plan — Challenge Before You Build

Catches expensive mistakes BEFORE agents write code. Combines scope challenge (is this the right thing?) with architecture review (is this the right way?). 10 minutes max.

**Team:** Steve (VP, orchestrator), Andy (backend), Ben Wang. Non-professional developers — output must be clear and visual.

## Usage

```
/review-plan SPEC-NNN      — Review a specific spec's approach
/review-plan               — List specs, ask which one
```

**When to run:**
- **Big Batch:** ALWAYS, before /decompose
- **Small Batch:** Skip UNLESS the spec touches 3+ tables

---

## Before Starting

1. Read the spec from `_Projects/Redoe-OS/_specs/SPEC-NNN-slug.md`
2. Read `_Projects/Redoe-OS/_specs/index.md` for related specs
3. Read `.claude/skills/spec/references/schema-quick-ref.md` for table context
4. Search the codebase for existing components/functions related to this spec (`grep`, `glob`)
5. **Search the Solutions Library:** Read `_Projects/Redoe-OS/docs/solutions/index.md` and scan for tags matching the spec's tables, tiers, and features. Surface relevant solutions: "SOLN-NNN covered a similar pattern — key gotcha was [X]."

---

## Phase 1: CEO Challenge

Ask these 5 questions. Present your finding for each, then ask Steve to confirm or push back. One at a time.

**1. Premise Check**
"What assumptions are we making that might be wrong?"
- List 2-3 assumptions embedded in the spec (inferred from the JTBD, data model, scope)
- Ask: "Which of these are validated? Which are we guessing?"

**2. Reuse Check**
"What already EXISTS that we could reuse instead of building new?"
- Search the repo for similar components, pages, hooks, RPCs, migrations
- Search existing specs for overlap
- Present findings: "Found [X] in [file] — could we extend this instead?"
- If nothing found, say so explicitly

**3. Right Thing Check**
"Is this the RIGHT thing to build, or just the thing we said we'd build?"
- Revisit the spec's JTBD and success criteria
- Ask: "If we could only ship ONE thing this week, is this still it?"
- If the spec's Pre-Mortem or Edge Cases suggest a different priority, flag it

**4. Alternative Approaches**
Propose 2-3 different ways to solve the problem. For each:
- One sentence describing the approach
- Pros/cons (2 each, max)
- Estimated complexity (Small Batch / Big Batch)
Lead with your recommendation. Ask Steve to pick.

**5. Dream State**
"Current state is [X]. This spec gets us to [Y]. 12-month ideal is [Z]. Does Y move toward Z, or is it a dead end?"
- Infer current state from spec's "Current Workaround" section
- Infer ideal from the broader Redoe OS vision
- Flag if the proposed solution creates tech debt or paints us into a corner

---

## Phase 2: Eng Architecture Review

Run these 5 checks. Report findings inline — don't wait until the end.

**1. Force a Diagram**
Generate at least ONE diagram in Mermaid syntax:
- **Data flow** — if the feature moves data between systems (SAP, Supabase, Lark)
- **Sequence diagram** — if the feature involves multi-step user flows or async operations
- **Component diagram** — if the feature adds new UI components

"A written spec can be vague. A sequence diagram CANNOT."

Show the diagram and ask: "Does this match what you had in mind?"

**2. Failure Mode Check + Error/Rescue Registry (v8)**
For each external dependency (Supabase, SAP, network, shared state):
- What happens when it fails?
- Who retries — user, system, or nobody?
- What's the fallback? (Degraded mode, error message, retry button)
- What does the error message say? (Propose actual copy)

**MANDATORY: Build an Error/Rescue Registry table.** Every error path must be explicitly documented BEFORE coding starts. This forces thinking about failure states, not just happy paths.

```markdown
## Error/Rescue Registry

| # | Error Condition | Source | Handler | User-Facing Message | Severity | Retry? |
|---|----------------|--------|---------|---------------------|----------|--------|
| 1 | Supabase query timeout | DB | Retry 3x, then error page | "Loading took too long. Tap to retry." | HIGH | Auto 3x |
| 2 | RLS policy blocks access | Auth | Redirect to 403 page | "You don't have access to this data. Contact your manager." | MEDIUM | No |
| 3 | WiFi drops mid-submit | Network | Queue locally, sync on reconnect | "Saved offline. Will sync when connected." | HIGH | Auto |
| 4 | SAP integration down | External | Degraded mode (show cached) | "SAP data may be outdated. Last sync: [time]." | LOW | Background |
```

Every row must have all 6 columns filled. No placeholders. If you don't know the handler, propose one — don't leave it blank.

This registry goes into the spec file under `## Error/Rescue Registry` and becomes the source of truth for error handling during implementation.

**3. Scope Smell Test**
Count the files this feature will touch.
- 1-4 files: Fine
- 5-7 files: Flag it, suggest simplification
- 8+ files: Too big. "This should be two specs." Propose the split.

Cross-reference against the spec's Appetite. If Small Batch touches 5+ files, challenge it.

**4. Integration Check**
"What other features/pages does this affect?"
- Check for shared components that would change
- Check for shared database tables (other specs touching the same tables)
- Check for shared RPC functions
- If impact found: "This also affects [feature X] — accounted for?"

**5. Performance Check**
"Will this be fast enough?"
- Queries: Will they perform with 10K rows? 100K rows?
- If the spec involves lists/tables: Is pagination planned?
- If the spec involves real-time: What's the update frequency?
- If Shop Floor tier: Page load must be <2s on tablet over WiFi

---

## Phase 3: Design Preview (MANDATORY for frontend changes)

**MANDATORY if** the spec touches any file in `apps/web/` — even if the "feature" is a backend change that surfaces in the UI.
**Skip ONLY if:** feature is purely database-only, API-only, or config with zero frontend impact.
**Source:** Redoe design system + UI UX Pro Max checklist.

**Auto-detect:** Check the spec's data model and affected tables. If any page, component, or route in `apps/web/src/` would change — this phase is mandatory. When in doubt, run it. Nobody ever regretted seeing a mockup before coding.

**The problem this solves:** Agent builds code that compiles and passes /qa — but the UI is ugly or wrong because nobody SAW it before coding. Same as reviewing a mold design before cutting steel.

**Process:**
1. Read `docs/DESIGN-SYSTEM.md` (or `_reference/design-system.md` in vault)
2. Based on the spec's tier, generate 2-3 quick wireframe concepts:
   - **Option A:** Minimal (fewest components, simplest layout)
   - **Option B:** Recommended (balanced)
   - **Option C:** Ambitious (if appetite allows)
3. Generate as **quick HTML mockups** — open in browser with `start "" "path"`. NOT production code. Fast and visual.
4. Show Steve. Ask: "Which direction? Or something different?"
5. If feedback: revise. Max 2 rounds.
6. Once approved: note chosen design in spec.

**What the mockup must show:**
- Layout structure (sidebar? tabs? single page?)
- Key components (data table? cards? form?)
- Tier-appropriate sizing (56px buttons for shop floor, dense tables for management)
- Status indicators (color + icon + text per design system)
- Empty state (zero data)
- Mobile/tablet view (if Shop Floor)

**What mockup does NOT need:**
- Real data (placeholder is fine)
- Working interactions (static is fine)
- Production styling (direction matters, not polish)
- Backend integration

**Design compliance checklist (from UI UX Pro Max, adapted for Redoe):**

Priority 1 — CRITICAL (must pass):
- [ ] Contrast 4.5:1 minimum (WCAG AA)
- [ ] Touch targets 44x44px minimum (56px for shop floor primary)
- [ ] 8px spacing grid
- [ ] No hover-only interactions
- [ ] Keyboard navigable (Tab, Enter, Escape)

Priority 2 — HIGH (flag if wrong):
- [ ] Font: DM Sans (headings/body), JetBrains Mono (data/numbers)
- [ ] Colors: Redoe palette only (#1F4E79, #2E75B6, #D6E4F0, status lime/amber/red)
- [ ] Status: color + icon + text (NEVER color alone)
- [ ] Tier-correct layout (shop floor = no sidebar, management = sidebar + Cmd+K)
- [ ] No financial data on shop floor views

Priority 3 — MEDIUM (advisory):
- [ ] Animations 150-300ms, ease-out, no bounce
- [ ] Empty state with message + CTA
- [ ] Loading state with skeleton shimmer
- [ ] Breadcrumbs clickable (not decorative)

**Steve approves the LOOK → then /decompose → agents build the CODE.**

---

## Output

After all phases, update the spec file with new sections:

```markdown
## Architecture
<!-- Mermaid diagram from Phase 2, Step 1 -->

## Alternatives Considered
| Approach | Pros | Cons | Verdict |
|----------|------|------|---------|
| A (recommended) | ... | ... | Selected |
| B | ... | ... | Rejected — [reason] |

## Failure Modes
| Dependency | Failure | Fallback | Error Copy |
|------------|---------|----------|------------|
| Supabase | Query timeout | Retry button | "Loading took too long. Tap to retry." |

## Assumptions Validated
- [x] [Assumption] — validated by [evidence]
- [ ] [Assumption] — NOT YET VALIDATED

## Approach: LOCKED
```

Write the updated spec back to the same file. Tell Steve: "Spec updated with architecture and alternatives. Ready for /decompose."

---

## Integration

- **`/spec`** defines what to build
- **`/review-plan`** challenges how to build it (this skill)
- **`/decompose`** breaks it into agent tasks
- **`/qa`** gates each task
- **`/retro`** captures what we learned

If /review-plan reveals the spec is too vague or too big, send Steve back to `/spec` or `/spec-review` first. Don't force a bad spec through the pipeline.

---

## Phase 4: Cross-Model Outside Voice (v7, OPTIONAL)

**When to run:** Big Batch features with 8+ files or architectural decisions. Skip for Small Batch.

**Purpose:** Get an independent cold read from another AI model to surface blind spots. Uses the existing `/council` skill.

**Process:**
1. Prepare a sanitized summary of the spec + architecture (no vault paths, no internal names)
2. Submit to `/council` with the prompt: "Review this feature architecture for a manufacturing ERP system. What failure modes, edge cases, or alternatives are we missing?"
3. Collect responses from ChatGPT + Gemini + Claude
4. **Tension Detection:** If models disagree on something, surface it explicitly:
   ```
   TENSION DETECTED:
   - ChatGPT recommends: [approach A]
   - Gemini recommends: [approach B]
   - Claude recommends: [approach C]

   The disagreement is about: [topic]
   My recommendation: [pick one with reasoning]
   ```
5. Integrate any valuable findings into the spec's Architecture or Failure Modes sections
6. Note in the spec: "Cross-model review completed [date]. Key findings: [summary]"

**What this catches:** Groupthink from a single model. Architecture patterns that work in theory but fail in manufacturing contexts. Edge cases that only emerge from different training data perspectives.

---

## Review Readiness Dashboard (v8)

After review-plan completes, write to `_workspace/review-status.json`:
```json
{
  "review_plan": {
    "completed": "2026-03-23T15:00:00Z",
    "commit": "<current HEAD short>",
    "phases_completed": ["ceo_challenge", "eng_review", "design_preview", "cross_model"],
    "error_registry_count": 4,
    "cross_model": true
  }
}
```
This is read by `/ship` to gate deployments.
