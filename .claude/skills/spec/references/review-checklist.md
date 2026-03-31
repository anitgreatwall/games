# Spec Review — 10-Point Checklist

Use this checklist to evaluate whether a spec is ready to build. Each item is PASS or FAIL.

## The Checklist

### 1. JTBD Clearly Stated
- PASS: Has "When ___, I want to ___, so I can ___" format with all three parts filled
- FAIL: Missing trigger, action, or payoff. Or uses vague "As a user, I want..."

### 2. Success Criteria Observable
- PASS: You can see or measure the outcome. "Operator logs time in under 30 seconds."
- FAIL: Vague feelings. "Time tracking is improved." "Users are happier."

### 3. Scope Boundaries Explicit
- PASS: "What This Does NOT Do" section exists with at least 2 concrete exclusions
- FAIL: Section missing, empty, or has only obvious exclusions ("does not launch rockets")

### 4. Data Model Identified
- PASS: Tables listed with operations (SELECT/INSERT/UPDATE/DELETE)
- FAIL: No tables listed, or tables listed without operations

### 5. RLS Tier Implications Noted
- PASS: States which roles can see/do what for each table touched
- FAIL: RLS not mentioned, or just says "uses RLS"

### 6. Appetite Set
- PASS: Explicitly says "Small Batch (1-2 days)" or "Big Batch (1-2 weeks)"
- FAIL: No appetite, or uses time estimates ("about 3 days") instead of batch size

### 7. Acceptance Criteria Testable
- PASS: Each criterion has [Actor] can [action] and [observable result] format
- FAIL: Criteria are vague ("works correctly"), missing actors, or not testable

### 8. Edge Cases Listed
- PASS: At least 2 "What if?" scenarios with expected behavior
- FAIL: No edge cases, or edge cases without expected behavior

### 9. Dependencies on Other Specs
- PASS: Dependencies section exists, states "none" or lists specific SPEC-NNN references
- FAIL: Section missing — unclear if this is standalone or depends on other work

### 10. AI Copilot Integration Considered
- PASS: States which RPCs are exposed (or explicitly "none")
- FAIL: Section missing — unclear if AI copilot should interact with this feature

## Scoring

- **10/10:** READY TO BUILD
- **7-9/10:** READY TO BUILD with minor gaps (note them)
- **4-6/10:** NEEDS WORK — fix failing items before building
- **0-3/10:** REWRITE — spec is too incomplete to act on
