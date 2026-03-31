---
name: decompose
description: Break a SPEC file into 2-5 atomic agent tasks with branches, file scopes, dependencies, and merge order. Feeds the Cherny-pattern parallel worktree workflow. Use when anyone says "decompose", "break this down", "split this spec", invokes /decompose, or after running /spec on a Big Batch feature.
---

# /decompose — Spec to Agent Tasks

Takes a SPEC-NNN file and breaks it into 2-5 atomic tasks, each assignable to a separate Claude Code agent in its own git worktree. This is the bridge between `/spec` (what to build) and the agent swarm (who builds what).

**Team:** Steve (VP, orchestrator), Andy (backend, monitors agents), Kevin (frontend), Ben Wang. Non-professional developers — output must be copy-paste ready.

## Usage

```
/decompose SPEC-001              — Decompose a specific spec
/decompose                       — List specs, ask which one
```

---

## Before Starting

1. Read the spec file from `_Projects/Redoe-OS/_specs/SPEC-NNN-slug.md`
2. Read `references/schema-quick-ref.md` for table context (in the /spec skill)
3. Read the design system summary (first 50 lines of `_reference/design-system.md`)
4. Check the spec's **Appetite** — Small Batch (2-3 tasks max) vs Big Batch (3-5 tasks)

## Decomposition Rules

### Task Types (in merge order)

Tasks MUST be typed. The type determines merge order — earlier types merge first because later types depend on them.

| Order | Type | Branch Prefix | What It Covers |
|-------|------|---------------|----------------|
| 1 | **Database** | `db/SPEC-NNN-slug` | Migrations, RPC functions, RLS policies, seed data |
| 2 | **Types** | (auto — merged with DB) | `supabase gen types` runs after DB merges. Not a separate task. |
| 3 | **API** | `feat/SPEC-NNN-slug-api` | Edge Functions, server actions, data fetching hooks |
| 4 | **UI** | `feat/SPEC-NNN-slug-ui` | Pages, components, layouts. Can split into multiple UI tasks. |
| 5 | **Test** | `test/SPEC-NNN-slug` | E2E Playwright tests. Only for Big Batch features. |

### Splitting Rules

1. **No two tasks touch the same file.** If they would, merge them into one task.
2. **Each task is independently mergeable** (after its dependencies).
3. **Database always goes first.** Other tasks depend on the types it generates.
4. **Small Batch = max 3 tasks.** Usually: DB + UI, or DB + API + UI.
5. **Big Batch = max 5 tasks.** DB + API + UI (split) + E2E.
6. **If a spec can't decompose cleanly, it needs splitting.** Flag this: "This spec should be two specs."

### File Scope

Each task must declare which directories/files the agent is allowed to touch. This prevents collisions.

```
Scope: supabase/migrations/, supabase/tests/
```

NOT:
```
Scope: the database stuff
```

### Naming Compliance

Every file path in the Scope section must follow `qa/references/naming-conventions.md`. Before writing the DECOMP file:
1. Read `qa/references/naming-conventions.md` for the full ruleset
2. Check every filename you generate against the rules (kebab-case HTML, YYYYMMDD migrations, etc.)
3. If the spec references a cryptic or legacy name (e.g., "the t38 page", "MM module", "a8 dashboard"), **translate it** to a descriptive kebab-case name in the decomposition:
   - `t38` → `time-entry-form.html`
   - `a8` → `attendance-summary.html`
   - `MM` → `material-management`
   - `AI_MM` → `ai-material-search.html`
4. Flag the rename explicitly in the task scope:
   > "Note: renaming `t38.html` → `time-entry-form.html` for naming compliance."
5. If you encounter a cryptic name NOT in the naming conventions reference, ask before proceeding:
   > "Cryptic name detected: `{name}`. What does this refer to? Need a descriptive kebab-case replacement."

### No Placeholders (NON-NEGOTIABLE)

Subagent quality is directly proportional to plan specificity. Every task must include enough detail that a subagent can execute without asking questions, stalling, or guessing.

**Every task MUST include:**
- **Exact file paths** — `Create: src/features/clock/clock-page.tsx`, `Modify: src/lib/supabase/queries.ts:45-60`
- **Complete code** — actual implementation, not descriptions of what to implement
- **Verification commands with expected output** — `Run: pnpm vitest src/features/clock/ — expect 4/4 pass`

**These are plan failures — NEVER produce them:**
- "TBD", "TODO", "implement later", "fill in details"
- "Add appropriate error handling" / "add validation"
- "Write tests for the above" (without actual test code)
- "Similar to Task N" (repeat the code — subagent may read tasks independently)
- Steps that describe WHAT without showing HOW

**Self-review gate:** Before saving the DECOMP file, scan every task for the failures above. If any are found, fix them inline before proceeding.

_Adapted from [obra/superpowers](https://github.com/obra/superpowers) writing-plans skill._

## Output Format

Write the decomposition to `_Projects/Redoe-OS/_specs/DECOMP-NNN-slug.md` (same NNN as the spec).

```markdown
# DECOMP-NNN: [Spec Title] — Task Breakdown

**Spec:** [[SPEC-NNN-slug]]
**Date:** YYYY-MM-DD
**Appetite:** Small Batch | Big Batch
**Total Tasks:** N
**Estimated Total Agent Time:** Xm

---

## Merge Order

```
Task 1 (DB) → merge → regen types → Task 2 (API) → merge → Task 3 (UI) → merge
```

## Task 1: [Descriptive Name]

**Type:** Database
**Branch:** `db/SPEC-NNN-slug`
**Scope:**
- `supabase/migrations/YYYYMMDD_description.sql`
- `supabase/tests/SPEC-NNN-slug.test.sql`

**Dependencies:** None
**Estimated Agent Time:** 15-20m

**Steps:**

- [ ] **Step 1:** Create migration file
  ```sql
  -- actual SQL here, not a description
  create table public.time_entries (
    id uuid primary key default gen_random_uuid(),
    ...
  );
  ```

- [ ] **Step 2:** Add RLS policies
  ```sql
  -- actual policies, not "add appropriate RLS"
  ```

- [ ] **Step 3:** Write pgTAP tests
  ```sql
  -- actual test code, not "write tests for the above"
  ```

- [ ] **Step 4:** Verify
  Run: `supabase db reset` — expect clean apply
  Run: `supabase test db` — expect all pass

---

## Task 2: [Descriptive Name]

**Type:** API | UI
**Branch:** `feat/SPEC-NNN-slug-api` | `feat/SPEC-NNN-slug-ui`
**Scope:**
- `apps/web/src/app/[route]/page.tsx`
- `apps/web/src/components/[feature]/[component].tsx`

**Dependencies:** Task 1 merged (needs generated types)
**Estimated Agent Time:** 30-45m

**Steps:**

- [ ] **Step 1:** Create page component
  ```tsx
  // actual component code, not "build the page"
  ```

- [ ] **Step 2:** Create feature components
  ```tsx
  // actual code for each component
  ```

- [ ] **Step 3:** Verify
  Run: `pnpm turbo run type-check` — expect 0 errors
  Run: `pnpm turbo run lint` — expect 0 errors
  Run: `/qa quick` — expect pass

---

[Repeat for each task]

## Agent Launch Commands

```bash
# Task 1
./scripts/agent-start.sh SPEC-NNN slug-db
# Then in the worktree: paste Task 1 instructions

# Task 2 (after Task 1 merges)
./scripts/agent-start.sh SPEC-NNN slug-ui
# Then in the worktree: paste Task 2 instructions
```

## Post-Merge Checklist

- [ ] All tasks merged to main in order
- [ ] Types regenerated after DB merge (`supabase gen types typescript`)
- [ ] `/regression` passes on main
- [ ] Tag release: `git tag YYYY.MM.N`
```

## After Generating

1. Write DECOMP file to `_Projects/Redoe-OS/_specs/DECOMP-NNN-slug.md`
2. Update `_Projects/Redoe-OS/_specs/index.md` — add decomposition entry under the spec
3. Show Steve the task breakdown and ask: "Does this split make sense? Any tasks you'd merge or split further?"
4. Once approved, Steve/Andy can run the agent launch commands

## Integration

- **`/spec`** produces the spec → **`/decompose`** breaks it into tasks → **agents build** in worktrees → **`/qa`** gates each PR → **`/regression`** validates main
- If `/decompose` finds the spec is too vague to split cleanly, send Steve back to `/spec-review` first
- Each task's Verification section maps directly to `/qa` checks — the agent runs these before creating a PR
