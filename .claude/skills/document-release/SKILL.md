---
name: document-release
description: "Auto-update project docs after shipping. Scans README, CLAUDE.md, inline comments, and API docs for stale references — wrong file paths, removed functions, outdated instructions, version mismatches. Runs automatically after /ship, or manually after any merge. Adapted from gStack /document-release pattern."
---

# /document-release — Keep Docs in Sync with Code

After code ships, docs go stale. This skill catches it before the team reads wrong instructions.

**Team:** Steve (VP), Andy (backend), Ben Wang. Non-dev team = stale docs cause real confusion.

## Usage

```
/document-release              — Scan and fix docs for current branch
/document-release --dry-run    — Report only (no edits)
/document-release --pr 42      — Scan docs affected by a specific PR
```

**When to run:**
- Automatically after `/ship` creates a PR (wired in /ship pipeline)
- After any manual merge to main
- When someone reports "the docs say X but the code does Y"

---

## What Gets Scanned

### Tier 1: Always Scan (critical docs)

| File | What to check |
|------|---------------|
| `CLAUDE.md` (all levels) | Stack versions, key paths, naming conventions, available skills list, design tokens |
| `README.md` | Getting started steps, install commands, project description |
| `_reference/DEV_PACK_VERSION` | Version matches actual dev pack |
| `_reference/design-system-cheatsheet.md` | Tokens match design-system.md |

### Tier 2: Scan If Changed (PR-scoped)

| File pattern | What to check |
|--------------|---------------|
| `supabase/migrations/*.sql` | Schema changes → check if CLAUDE.md mentions affected tables |
| `apps/web/src/**/*.tsx` | Component renames/deletes → check if docs reference old names |
| `package.json` | Dependency changes → check if README references old packages |
| `.github/workflows/*.yml` | CI changes → check if deploy docs are still accurate |

### Tier 3: Deep Scan (monthly or major releases)

| Target | What to check |
|--------|---------------|
| All inline `// TODO` and `// FIXME` | Any that reference completed work? Remove them. |
| All `@deprecated` annotations | Is the deprecated thing actually removed? Clean up. |
| All skill SKILL.md files | Do usage examples still work? Are referenced files still present? |

---

## The Process

### Step 1: Identify What Changed

```bash
# Get files changed in the PR or since last release
git diff main --name-only
```

Categorize changes:
- **Schema changes** (migrations/) → check table/column references in docs
- **Component changes** (src/) → check component references in docs
- **Config changes** (package.json, tsconfig, etc.) → check setup instructions
- **Skill changes** (.claude/skills/) → check skill lists in CLAUDE.md
- **Path changes** (file moves/renames) → check all path references

### Step 2: Scan for Staleness

For each changed file, grep the doc files for references:

```bash
# Example: if src/components/job-list-table.tsx was renamed to job-table.tsx
grep -r "job-list-table" CLAUDE.md README.md .claude/ --include="*.md"
```

**Staleness signals:**
- File path in docs → file doesn't exist
- Function name in docs → function renamed or deleted
- Version number in docs → doesn't match VERSION or package.json
- "Available skills" list → skill added or removed
- Setup commands → dependency or config changed
- Design tokens → values changed in design-system.md

### Step 3: Fix or Report

For each finding:

1. **Auto-fixable** (path renames, version bumps, skill list updates):
   - Make the edit directly
   - Stage as atomic commit: `docs: update [file] — [what changed]`

2. **Needs review** (rewritten instructions, removed features, changed workflows):
   - Add to report with suggested new text
   - Flag for human review

3. **Ambiguous** (doc references something that was refactored, unclear replacement):
   - Add to report as "NEEDS HUMAN: [description]"

---

## Output

```
=========================================
DOCUMENT RELEASE — Redoe OS
=========================================
PR:          #42 (feat/SPEC-005-attendance-report)
Files changed: 12
Docs scanned:  8
Findings:      4

Auto-Fixed:
────────────────────────────────────────
1. CLAUDE.md:47 — Updated key path: apps/web/src/attendance/ → apps/web/src/time-tracking/
2. README.md:23 — Version bump: 2026.03.2 → 2026.03.3
3. CLAUDE.md:112 — Added /attendance-report to available pages list

Needs Review:
────────────────────────────────────────
4. CLAUDE.md:78 — Design token section references `attendance-card` component
   which was split into `attendance-summary` and `attendance-detail`.
   Suggested: Update component reference to list both new components.

No Action Needed:
────────────────────────────────────────
- design-system-cheatsheet.md — no affected tokens
- DEV_PACK_VERSION — already current (v13.0.0)
=========================================
```

---

## Integration

- **`/ship`** — auto-invokes `/document-release` after PR creation (pre-merge docs update)
- **`/retro`** — if stale docs caused team confusion, feed into retro
- **`/qa`** — Stage 0 naming lint catches file path mismatches; this skill catches doc-level mismatches
- **`/verify`** — can add doc freshness to completion manifests

---

## Anti-Patterns (Don't Do This)

- Don't rewrite docs for style — only fix factual staleness
- Don't add new documentation — this skill updates existing docs, not creates new ones
- Don't touch user-facing content (marketing, onboarding) — code docs only
- Don't auto-fix ambiguous cases — flag for human review
- Don't run on every commit — run after `/ship` or on major merges
