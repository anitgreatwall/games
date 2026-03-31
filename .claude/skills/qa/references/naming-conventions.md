# Redoe OS Naming Conventions — Canonical Reference

> Read by `/qa` (Stage 0), `/code-review`, and `/decompose`. This is the single source of truth.

## File Naming Rules

| Type | Convention | Good | Bad |
|------|-----------|------|-----|
| HTML app files | `kebab-case.html`, min 2 words, descriptive | `attendance-dashboard.html` | `a8.html`, `attendancedashboard.html`, `AI_MM.html` |
| SQL migrations | `YYYYMMDD_snake_description.sql` | `20260323_create_bug_reports.sql` | `bugfix.sql`, `20260323-bug-reports.sql` |
| JS/TS source | `kebab-case.js` or `kebab-case.ts` | `job-tracker.ts`, `time-entry.js` | `JobTracker.ts`, `time_entry.js` |
| Service files | `REDOE-{name}-svr.js` (legacy convention) | `REDOE-proxy-svr.js` | `proxy-server.js`, `REDOE_proxy.js` |
| React components | `PascalCase.tsx` (if using React/Next.js) | `JobTracker.tsx` | `job-tracker.tsx`, `jobTracker.tsx` |
| Spec files | `SPEC-NNN-slug.md` (kebab-case slug, 2-5 words) | `SPEC-001-employee-management.md` | `SPEC-001.md`, `spec-employee.md` |
| Decomp files | `DECOMP-NNN-slug.md` (matches parent spec) | `DECOMP-001-employee-management.md` | `decomp-1.md` |
| Solution files | `SOLN-NNN-slug.md` (kebab-case slug) | `SOLN-003-rls-service-role.md` | `solution3.md` |
| CSS/style files | `kebab-case.css` | `shop-floor.css` | `ShopFloor.css` |
| Test files | `{feature}.test.sql` or `{feature}.test.ts` | `employee.test.sql` | `test1.sql` |

## Folder Naming Rules

| Location | Convention | Good | Bad |
|----------|-----------|------|-----|
| `apps/{feature}/` | **lowercase kebab-case** | `apps/time-tracking/` | `apps/TimeTracking/`, `apps/MM/` |
| `docs/{category}/` | **UPPERCASE** (top-level doc categories only) | `docs/AI/`, `docs/DB/` | `docs/ai/`, `docs/Ai/` |
| `supabase/migrations/` | Fixed path, don't rename | — | — |
| `_Projects/` | As-is (vault convention) | — | — |
| New feature folders | **lowercase kebab-case** | `apps/bug-report/` | `apps/BugReport/` |

## Variable/Identifier Naming

| Context | Convention | Good | Bad |
|---------|-----------|------|-----|
| SQL tables, columns | `snake_case` | `job_milestones`, `created_at` | `jobMilestones`, `CreatedAt` |
| SQL functions | `fn_snake_case` | `fn_get_active_jobs` | `getActiveJobs`, `get_active_jobs` |
| SQL triggers | `trg_snake_case` or `audit_table` | `audit_employees`, `trg_update_status` | `updateTrigger` |
| JS variables, functions | `camelCase` | `getActiveJobs`, `jobStatus` | `get_active_jobs`, `JobStatus` |
| JS constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` | `maxRetryCount` |
| CSS classes | Tailwind utilities | `bg-slate-950 text-white` | `.header-blue { ... }` |
| Branch names | `type/SPEC-NNN-slug` or `type/description` | `feat/SPEC-001-time-entry-ui` | `feature/timeEntry`, `steve/wip` |

## Banned Patterns

These FAIL `/qa` unconditionally:

| Pattern | Why |
|---------|-----|
| Spaces in filenames | Breaks shell scripts, URLs, imports |
| `New Text Document.txt`, `New Microsoft *.xlsx/docx` | Default Windows junk — not real files |
| `Untitled*`, `Copy of *`, `* (1).*` | Accidental duplicates |
| `-backup`, `-copy`, `-old`, `-bak` suffixes | Use git for versioning, not filename suffixes |
| Chinese/non-ASCII characters in filenames | Breaks cross-platform paths. Use English filenames with Chinese content inside. |
| Single-character or number-only filenames | `a8.html`, `t38.html` — must be descriptive |
| Mixed separators in one name | `AI_MM-Manual.html` — pick one convention |
| `.env`, `credentials.json`, `*.pem` without `.gitignore` | Secrets must never be committed |

## Cryptic Name Translation

When a spec or existing code uses a cryptic internal name, `/decompose` must translate it:

| Cryptic | Descriptive | Context |
|---------|------------|---------|
| `t38` | `time-entry-form` | Time tracking form (originally SAP form T38) |
| `a8` | `attendance-summary` | Attendance report (originally SAP report A8) |
| `MM` | `material-management` | Material management module |
| `AI_MM` | `ai-material-search` | AI-powered material search |

When encountering a NEW cryptic name not in this table, flag it:
> "Cryptic name detected: `{name}`. What does this refer to? Need a descriptive kebab-case replacement before proceeding."

Update this table when new translations are established.

## How This Is Enforced

1. **`/qa` Stage 0 (Naming Lint)** — checks every new/renamed file against these rules. Fails the build on violations.
2. **`/code-review` checklist** — includes a naming section that reviewers check.
3. **`/decompose`** — generates correct filenames in task Scope sections, translates cryptic names.
4. **`/qa fix`** — can auto-rename files that violate conventions (with git mv).
