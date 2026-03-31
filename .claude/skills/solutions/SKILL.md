---
name: solutions
description: "Knowledge compounding library for Redoe OS. After every shipped feature, captures what was solved and how — stored as searchable docs that /spec and /review-plan auto-query before planning. The more you build, the smarter planning gets."
---

# /solutions — Compound What You Learn

Every shipped feature teaches something. This skill captures it in a searchable format so future planning starts smarter, not from scratch.

**Team:** Steve (VP), Andy (backend), Ben Wang. Solutions are written for the NEXT person to touch this area — not the person who just built it.

**Core rule:** If `/retro` identified a lesson, `/solutions` makes it findable. Retros without solutions are journal entries. Solutions without retros are guesses.

## Usage

```
/solutions                     — Write a solution doc (interactive)
/solutions [topic]             — Write a solution doc with topic pre-loaded
/solutions search [query]      — Search existing solutions
/solutions refresh             — Re-evaluate existing docs for staleness
```

---

## When to Run

- **After `/retro`** — mandatory. Every retro produces at least one solution doc.
- **After solving a non-obvious problem** — if it took more than 30 minutes to figure out, document it.
- **After discovering undocumented behavior** — Supabase quirks, RLS edge cases, Next.js gotchas.

---

## Writing a Solution Doc

### Step 1: Identify the Pattern

Ask: "What did we solve that someone will hit again?"

Not every bug fix is a solution. A typo fix is not. But "RLS policies don't apply to service_role queries" IS — because the next person writing an RLS policy will hit the same wall.

**Good solutions answer:** "If you're trying to do X, here's what we learned."

### Step 2: Write the Doc

Read `references/solution-template.md` for the format. Create the file at:

```
_Projects/Redoe-OS/docs/solutions/SOLN-NNN-slug.md
```

Get the next number from `_Projects/Redoe-OS/docs/solutions/index.md` (create if missing).

**Required fields:**
- **Title** — What was solved (searchable, specific)
- **Category** — `database`, `frontend`, `auth`, `infrastructure`, `integration`, `workflow`, `design-system`
- **Tags** — Specific technologies, patterns, or concepts (e.g., `rls`, `supabase`, `shift-change`, `offline`)
- **Problem** — What went wrong or what was hard (1-3 sentences)
- **Solution** — What we did (specific enough to reproduce)
- **Key Decision** — Why this approach over alternatives
- **Gotchas** — What to watch out for next time

**Optional fields:**
- **Related specs** — SPEC-NNN references
- **Files touched** — Key files involved
- **Time cost** — How long the original problem took to solve

### Step 3: Update the Index

Add a one-line entry to `_Projects/Redoe-OS/docs/solutions/index.md`:

```markdown
- [SOLN-NNN](SOLN-NNN-slug.md) — One-line description [category] [tags]
```

---

## Searching Solutions

When `/spec` or `/review-plan` starts, they search solutions automatically:

1. Extract key terms from the spec topic (tables, tiers, features)
2. Search `docs/solutions/index.md` for matching tags/categories
3. Read matching solution docs
4. Surface relevant findings: "We solved something similar before — see SOLN-003"

The search is keyword-based against YAML frontmatter tags + title. Keep tags specific and consistent.

### Manual Search

```
/solutions search rls          — Find all RLS-related solutions
/solutions search shift-change — Find shift-change edge cases
/solutions search supabase     — Find Supabase-specific gotchas
```

---

## Refreshing Solutions (`/solutions refresh`)

Run monthly (or during `/retro weekly`):

1. Read all solution docs in `docs/solutions/`
2. For each doc, check:
   - **Still accurate?** — Has the codebase changed in a way that invalidates this?
   - **Still relevant?** — Is this problem still possible, or did we fix the root cause?
   - **Needs update?** — Has our understanding improved since writing this?
3. Mark stale docs with `status: stale` in frontmatter
4. Update or archive as needed

---

## Integration

```
/spec → (searches solutions before Q1)
/review-plan → (searches solutions before Phase 1)
/retro → /solutions (mandatory — every retro produces at least one)
```

- **`/retro`** calls `/solutions` after Step 3 (feedback loop)
- **`/spec`** searches solutions in "Before Starting" phase
- **`/review-plan`** searches solutions in "Before Starting" phase
- Solutions live in the Redoe OS repo, not the skill pack — they're project-specific knowledge

---

## What This Compounds

Week 1: 0 solutions. Planning starts cold.
Week 4: 10 solutions. Planning catches 2 known gotchas before they waste time.
Week 12: 30+ solutions. Planning is informed by 3 months of institutional knowledge.
Week 26: The system knows more about Redoe OS than any single team member.

This is the flywheel. Every other skill gets smarter because this one remembers.
