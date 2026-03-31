---
name: spec
description: "Best-in-class product spec tool for non-developer teams (v8). Three modes — /spec (10 questions + challenge + adversarial review loop → spec file), /interview (user discovery → interview summary), /spec-review (14-point gap checker). Forces structured thinking before coding. Writes to Review Readiness Dashboard for /ship gating. Patterns from: Shape Up, Amazon PR/FAQ, Cagan 4 Risks, Klein Pre-Mortem, Osmani (O'Reilly)."
---

# /spec — Think Before You Build

Product spec for the Redoe OS team. 10 structured questions across 4 phases — problem discovery, scope, edge cases, and a challenge round that pushes back before locking.

**Team:** Steve (VP), Andy (backend), Ben Wang. None are professional developers. This must feel like a sharp 10-minute PM conversation, not a bureaucratic form.

**Core rule:** Spend 70% of effort defining the problem, 30% on execution (Karpathy). This skill IS the 70%.

<HARD-GATE>
Do NOT implement anything, write any code, or invoke /decompose until the spec is written and the user has approved it. This applies to EVERY feature regardless of perceived simplicity. "Simple projects are where unexamined assumptions cause the most wasted work." (superpowers)
</HARD-GATE>

## Three Modes

```
/spec              — Feature spec (10 questions → spec file)
/spec [topic]      — Same, with topic pre-loaded
/interview         — User discovery (6 questions → interview summary)
/interview [name]  — Same, with interviewee name pre-loaded
/spec-review       — Gap check on existing spec (14-point checklist)
/spec-review SPEC-NNN — Check specific spec
```

---

## Mode 1: /spec — Feature Spec Generator

**Time:** 10 minutes. **Output:** `_Projects/Redoe-OS/_specs/SPEC-NNN-slug.md`

### Before Starting
1. Read `references/spec-template.md` for the output format
2. Read `references/schema-quick-ref.md` for table/tier auto-suggestions
3. Check `_Projects/Redoe-OS/_specs/index.md` for the next SPEC number
4. **Search the Solutions Library:** Read `_Projects/Redoe-OS/docs/solutions/index.md` and scan for tags matching the topic. If relevant solutions exist, read them and surface findings: "We solved something similar before — see SOLN-NNN." This prevents re-learning lessons the team already paid for.

### Ask These 10 Questions (4 Phases)

One question at a time. Wait for the answer before moving on. Keep it conversational. If the user gives a vague answer, push back once — "can you be more specific?" Prefer multiple choice when possible. Accept "I don't know" — that's better than a guess.

---

#### Phase 1: Problem Discovery (Q1-Q4)

**Q1: Who is this for?**
Present the options:
- Shop Floor (cnc_operator, moldmaker, edm_operator, inspector)
- PM (pm, scheduler)
- Finance (finance, buyer)
- Management (gm, vp, plant_mgr, engineering_mgr, sales)
- All

**Q2: What are they doing TODAY to solve this?**
The status quo is the real competitor — not other software.
- "How do they handle this right now — even badly? Paper? Excel? Walking to someone's desk? Yelling across the shop?"
- "What does that workaround cost them — time, errors, frustration?"
- If Steve says "nothing, they don't do it" — push back: "So they just live with the problem? What happens when it bites them?"

**Q3: What's the job to be done?**
Help them frame it as: "When ___, I want to ___, so I can ___"
- Example: "When I finish a CNC operation, I want to log my hours on my phone, so I can go home without waiting for the office to close."
- If they struggle: "What's the trigger? What do they do? What's the payoff?"

**Q4: What does success look like?**
Must be observable, not vague. Push back on "it works better" or "they're happier."
- Good: "Operator logs time in under 30 seconds without typing a job number"
- Bad: "Time tracking is improved"

---

#### Phase 2: Scope & Boundaries (Q5-Q7)

**Q5: What does this NOT do?**
The most important question. Prevents scope creep and rework.
- "What might someone assume this includes, but it shouldn't?"
- Example: "Does NOT replace the paper F738. Does NOT auto-calculate overtime. Does NOT sync to SAP."
- Push for at least 3 explicit exclusions.

**Q6: What's the appetite?** *(Shape Up)*
Two options only:
- **Small Batch** (1-2 days) — bug fix, simple UI change, one-table feature
- **Big Batch** (1-2 weeks) — multi-table feature, new workflow, new dashboard

This is "how much time is this WORTH?" not "how long will it take?" The appetite constrains the solution.

If the user says Small Batch but it sounds like Big Batch: "This touches 4 tables and a new workflow — that's Big Batch territory. Want to split it, or give it the full 1-2 weeks?"

**Q7: What data does it touch?**
Auto-suggest tables from `references/schema-quick-ref.md` based on Q1-Q6 answers.
- Present the relevant tables with their RLS tier
- Ask: "Does this look right? Anything missing?"

---

#### Phase 3: Edge Cases & Risk (Q8-Q9) — The Round Most People Skip

**Q8: What could go wrong?** *(Klein Pre-Mortem + Redoe edge cases)*
Propose 3-5 edge cases based on Q1-Q7 answers. Pull from the Redoe-specific list AND the specific scenario:

Redoe-specific edge cases to always consider:
- **Shift change:** Task carries from day to night shift?
- **Gloves/PPE:** Touch targets must be 48px+. Are we building for gloves?
- **WiFi drops:** Shop floor tablets lose connectivity. Queue locally?
- **Shared kiosk:** Two operators, one tablet. Identity switching?
- **SAP/Supabase down:** Degraded mode or error page?
- **Cold start:** System is new — what does this look like with zero data?
- **Bilingual:** Windsor = English. Hunan = Chinese. Need both?
- **Time zones:** Windsor (ET) vs Hunan (CST+8). Time-sensitive?
- **Backward Q2C:** SO created AFTER job starts. Data available?
- **Rework loop:** Inspector fails a part — does this feature handle re-entry?

Present the relevant ones (not all 10 — pick the 3-5 that apply). Ask:
"Which of these matter for this feature? Anything I'm missing?"

**Q9: Pre-mortem** *(Klein — increases failure identification by 30%)*
One question: "Imagine it's 3 months from now. This feature launched and NOBODY uses it — or worse, it caused problems. What went wrong?"

Let the user think. Their answer reveals the real risks they haven't articulated. If they say "I don't know" — offer 2-3 scenarios: "Maybe the operators found it slower than paper? Maybe the data was wrong because of X? Maybe nobody trained them?"

---

#### Phase 4: Challenge & Lock (Q10) — The Pushback Round

**Q10: The challenge**
Challenge the spec ONCE before locking. Pick the most relevant pushback:

- **Scope smell:** "You said Small Batch but this touches [N] tables and [M] pages — are you sure?"
- **Overlap:** "This overlaps with SPEC-[NNN] — should they be merged?"
- **Tier mismatch:** "You said Shop Floor but you're asking for data tables with sorting — are you sure this isn't Management tier?"
- **Narrowest wedge:** "What's the SMALLEST version of this that someone would actually use THIS WEEK?"
- **Assumption check:** "The most expensive assumption here is [X]. Have you validated it?"
- **Status quo win:** "The current workaround [from Q2] has worked for [N] years. Why is NOW the time to fix it?"
- **Demand reality:** "Who would be genuinely upset if we DIDN'T build this?"

ONE challenge. User responds. Then lock the spec.

---

### After All 10 Questions

1. Generate the spec using `references/spec-template.md`
2. Auto-fill: affected RLS tiers, related tables, AI Copilot hooks (if applicable)
3. Auto-assess Cagan's 4 risks based on Q1-Q10 answers:
   - Value risk (from Q2 status quo + Q9 pre-mortem)
   - Usability risk (from Q1 tier + Q8 edge cases)
   - Feasibility risk (from Q6 appetite + Q7 data)
   - Business viability risk (from Q5 non-goals + Q10 challenge)
4. Cross-reference existing specs in `_Projects/Redoe-OS/_specs/index.md` — flag overlaps

### Adversarial Spec Review Loop (v8)

After generating the spec, run a Red Team review. This catches blind spots before the spec is locked.

5. **Spawn a review subagent** that scores the spec on 5 dimensions (1-10 each):

| Dimension | What it checks | Fail threshold |
|-----------|---------------|---------------|
| **Completeness** | All 14 checklist items addressed? Missing sections? | < 7 |
| **Feasibility** | Can this be built within the stated appetite? File count realistic? | < 7 |
| **Edge Cases** | Are the Redoe-specific edge cases (shift change, gloves, WiFi, kiosk) addressed? | < 7 |
| **Security** | RLS implications clear? Financial data exposure considered? | < 7 |
| **Testability** | Can every acceptance criterion be verified by /qa? Observable outcomes? | < 7 |

6. **If ANY dimension scores < 7/10:** revise the spec to address the gaps. Re-score. Max 3 iterations.
7. **Convergence guard:** If after 3 passes a dimension still fails, flag it as "KNOWN GAP" in the spec with a mitigation note. Don't loop forever.
8. Write the spec file to `_Projects/Redoe-OS/_specs/SPEC-NNN-slug.md`
9. Update `_Projects/Redoe-OS/_specs/index.md` with the new entry
10. Show the user the completed spec with review scores and ask: "Anything to change before we lock this in?"
11. **Generate HTML wireframe** — For any feature with a visual component, create a self-contained HTML wireframe showing the key screens at the declared tier's target viewport. Save to `_Projects/Redoe-OS/_specs/wireframes/SPEC-NNN-wireframe.html`. Open in browser for Steve to review alongside the spec. Use `references/wireframe-template.html` as the base template. Gray-box layout with dashed borders, `WIREFRAME — NOT FINAL` banner. Show structure and layout, not final design. This is the visual contract between spec and implementation.

### Review Readiness Dashboard (v8)

After spec is locked, write to `_workspace/review-status.json`:
```json
{
  "spec": {
    "completed": "2026-03-23T14:00:00Z",
    "commit": "<current HEAD short>",
    "id": "SPEC-NNN",
    "review_scores": { "completeness": 9, "feasibility": 8, "edge_cases": 8, "security": 9, "testability": 7 }
  }
}
```
This is read by `/ship` to gate deployments.

---

## Mode 2: /interview — User Discovery

**Time:** 10 minutes per interview. **Output:** `_Projects/Redoe-OS/_specs/interviews/INT-NNN-name.md`

### Purpose
For interviewing real users on the shop floor, in the PM office, or in finance. Extracts pain points and feature candidates from how people actually work — not how we think they work. Use temporal prompts ("tell me about the LAST TIME..."), not hypotheticals (Teresa Torres).

### Before Starting
1. Read `references/interview-template.md` for the output format
2. If interviewee has a People file in `02_People/`, read it for context
3. Ask Steve: "What topic are we exploring?" (e.g., time tracking, job status, quoting)

### Ask These 6 Questions

Conversational, open-ended. Let them talk. Take notes, don't interrupt. If they go off-topic, gently steer back.

**Q1: "Walk me through your day — what do you do first when you get in?"**
Establishes baseline workflow. Listen for: tools used, handoffs, bottlenecks, workarounds.

**Q2: "What's the most annoying part of [topic]?"**
Replace [topic] with the focus area. Listen for: complaints, frustration, time wasted.

**Q3: "Show me how you do [task] right now."**
If in person, observe. If remote, ask them to describe step-by-step. Listen for: paper forms, Excel, walking to someone's desk, duplicate entry. "The status quo is your real competitor" — understand it deeply.

**Q4: "What happens when it goes wrong?"**
Listen for: error recovery, blame, workarounds, who they call, how long it takes to fix.

**Q5: "If you could change one thing about [topic], what would it be?"**
One thing only. Forces prioritization. The answer is usually the #1 feature candidate.

**Q6: "What did I not ask that I should have?"** *(Teresa Torres)*
Often surfaces the real problem. Don't skip this.

### After the Interview
1. Write the interview summary using `references/interview-template.md`
2. Extract: pain points (ranked), current workarounds, feature candidates
3. Cross-reference against existing specs — link any that address discovered pain points
4. File to `_Projects/Redoe-OS/_specs/interviews/INT-NNN-name.md`
5. Update `_Projects/Redoe-OS/_specs/index.md`
6. Surface top finding to Steve: "The #1 thing [name] wants is ___. We [have/don't have] a spec for that."

---

## Mode 3: /spec-review — Gap Checker

**Time:** 2 minutes. **Input:** Existing spec file. **Output:** Pass/fail checklist.

### Before Starting
1. Read `references/review-checklist.md` for the 14-point checklist
2. If no spec specified, list available specs from `_Projects/Redoe-OS/_specs/index.md` and ask which one

### Run the 14-Point Checklist

Read the spec file and evaluate each point. For each item, output PASS or FAIL with a one-line explanation.

**Core (original 10):**
1. **JTBD clearly stated?** — Has "When ___, I want to ___, so I can ___" format
2. **Success criteria observable?** — Can you see/measure it, not just feel it
3. **Scope boundaries explicit?** — "What This Does NOT Do" section exists with 3+ entries
4. **Data model identified?** — Tables listed with RLS tiers
5. **RLS tier implications noted?** — Which roles can see/do what
6. **Appetite set?** — Small Batch or Big Batch declared, consistent with scope
7. **Acceptance criteria testable?** — Each criterion has actor + action + observable result
8. **Edge cases listed?** — At least 2 "what if" scenarios, USER-VALIDATED (not auto-generated)
9. **Dependencies on other specs?** — Cross-references checked
10. **AI Copilot integration considered?** — Which RPCs (if any) this feature exposes

**New (v2):**
11. **Current workaround documented?** — Do we know what users do today?
12. **Edge cases validated by user?** — Discussed in interview, not just auto-generated by Claude
13. **Pre-mortem completed?** — At least 2 failure scenarios identified and addressed
14. **Challenge question addressed?** — At least one pushback resolved before locking

### Output Format
```
SPEC-NNN Review
===============
1.  JTBD              [PASS/FAIL] — explanation
2.  Success Criteria   [PASS/FAIL] — explanation
3.  Scope Boundaries   [PASS/FAIL] — explanation
4.  Data Model         [PASS/FAIL] — explanation
5.  RLS Tiers          [PASS/FAIL] — explanation
6.  Appetite           [PASS/FAIL] — explanation
7.  Acceptance Criteria[PASS/FAIL] — explanation
8.  Edge Cases         [PASS/FAIL] — explanation
9.  Dependencies       [PASS/FAIL] — explanation
10. AI Copilot         [PASS/FAIL] — explanation
11. Current Workaround [PASS/FAIL] — explanation
12. Edge Case Validation[PASS/FAIL] — explanation
13. Pre-Mortem         [PASS/FAIL] — explanation
14. Challenge Resolved [PASS/FAIL] — explanation

Score: X/14
Verdict: READY TO BUILD / NEEDS WORK
```

If NEEDS WORK, suggest specific fixes for each FAIL item.

---

## Integration with Other Skills

- **`/review-plan`:** After spec is locked, run /review-plan for Big Batch features to challenge the approach and force architecture diagrams.
- **`/decompose`:** After spec (and optionally /review-plan), run /decompose to break into parallel agent tasks.
- **`/qa` Stage 4:** Code review cross-references specs. When a PR touches a table listed in a spec, the reviewer checks acceptance criteria.
- **`/retro`:** After feature ships, /retro feeds findings back into this skill — edge cases we missed become permanent additions.
- **AI Copilot RPCs:** Specs note which of the 6 RPC tools the feature should expose.
- **Schema Guardian:** When a migration adds tables, check if there's a matching spec. No spec = warning.

---

## Spec Numbering

- Feature specs: `SPEC-001`, `SPEC-002`, etc. (sequential)
- Interviews: `INT-001`, `INT-002`, etc. (sequential)
- Slugs: lowercase, hyphenated, descriptive (e.g., `time-tracking`, `job-cost-dashboard`)
- Files: `SPEC-001-time-tracking.md`, `INT-001-cnc-operator-jimmy.md`
