---
name: careful
description: "Safety guardrails for Redoe OS development. Intercepts destructive commands (rm -rf, DROP TABLE, force-push, git reset --hard) and warns before executing. Common build cleanups are whitelisted. Designed for non-professional developer teams — prevents one bad command from wiping work. Implement as a PreToolUse hook."
---

# /careful — Safety Guardrails

Prevents destructive commands from running without explicit confirmation. Built for non-dev teams where one bad command can wipe hours of work.

**Team:** Steve (VP), Andy (backend), Ben Wang. None are professional developers. Safety net is mandatory.

## Usage

```
/careful              — Show current guardrail status and rules
/careful --enable     — Enable guardrails (default: ON for all sessions)
/careful --disable    — Disable temporarily (re-enables next session)
/careful --log        — Show blocked command history
```

**How it works:** Implemented as a `PreToolUse` hook on `Bash` commands. Every shell command is checked against the blocklist before execution. Blocked commands require explicit user confirmation.

---

## Implementation

Add to `.claude/settings.json` in the project:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/careful-guard.sh \"$TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

### Hook Script: `.claude/hooks/careful-guard.sh`

The hook receives the Bash tool input as JSON. It extracts the command and checks it against the blocklist.

**Block with confirmation required:**

| Category | Patterns | Why |
|----------|----------|-----|
| File deletion | `rm -rf`, `rm -r`, `rmdir`, `del /s` | Can wipe entire directories |
| Git destructive | `git reset --hard`, `git push --force`, `git push -f`, `git checkout -- .`, `git clean -fd` | Loses uncommitted work or overwrites remote |
| Git branch delete | `git branch -D`, `git push origin --delete` | Can delete unmerged work |
| Database drop | `DROP TABLE`, `DROP DATABASE`, `DROP SCHEMA`, `TRUNCATE` | Irreversible data loss |
| Supabase reset | `supabase db reset`, `supabase stop` | Wipes local dev database |
| Process kill | `kill -9`, `killall`, `taskkill /f` | Can kill dev servers or background jobs |
| Permission change | `chmod 777`, `chmod -R` | Security risk |
| Package nuke | `rm -rf node_modules`, `rm package-lock.json`, `rm pnpm-lock.yaml` | Use proper package manager commands instead |

**Allowed (whitelisted — no confirmation):**

| Pattern | Why |
|---------|-----|
| `rm -rf .next/` | Standard Next.js build cleanup |
| `rm -rf dist/`, `rm -rf build/` | Standard build output cleanup |
| `rm -rf .turbo/` | Turborepo cache cleanup |
| `git stash` | Non-destructive (saves work) |
| `git checkout [branch-name]` | Switching branches (not `git checkout -- .`) |
| `pnpm store prune` | Package manager cache cleanup |
| `supabase gen types` | Type generation (read-only) |

---

## Alert Format

When a blocked command is intercepted:

```
⚠️  CAREFUL — Destructive command detected
────────────────────────────────────────────
Command:   rm -rf supabase/migrations/
Category:  File deletion
Risk:      Deletes all SQL migration files — this is IRREVERSIBLE

Safer alternatives:
  • git stash — save changes without deleting
  • mv supabase/migrations/ /tmp/migrations-backup/ — move to temp instead

To proceed anyway: re-run the command with CAREFUL_ALLOW=1 prefix
────────────────────────────────────────────
```

---

## Escalation Rules

| Severity | Command type | Action |
|----------|-------------|--------|
| **BLOCK** | `DROP TABLE`, `git push --force main`, `rm -rf /` | Always block. No override. |
| **WARN** | `rm -rf [project-dir]`, `git reset --hard` | Block with confirmation. Show safer alternative. |
| **INFO** | `git branch -d` (lowercase d = safe delete), `rm` single file | Log only. Don't block. |

---

## Agent-Specific Rules

When running inside `/decompose` parallel worktree agents:

1. **Agents cannot delete files outside their assigned scope.** Block any `rm` on files not in the agent's task Scope section.
2. **Agents cannot force-push.** Only the main session (via `/ship`) can push.
3. **Agents cannot modify `.claude/` or `_workspace/` config files.** These are shared state.
4. **Agents cannot run `supabase db reset`.** Database is shared across all agents.

---

## Integration

- **`/freeze`** — `/careful` blocks dangerous commands globally; `/freeze` restricts edits to a specific directory. Use both for maximum safety.
- **`/ship`** — `/careful` is automatically more permissive during `/ship` (allows force-push to feature branches, allows branch deletion after merge).
- **`/investigate`** — auto-enables `/careful` to prevent "fix by deleting" anti-pattern.
- **All agent sessions** — `/careful` should be enabled by default in all `.claude/settings.json`.

---

## What This Prevents

Real incidents this guardrail would have caught:
- Agent running `rm -rf supabase/` instead of `rm -rf supabase/.temp/`
- `git reset --hard` that wiped 2 hours of uncommitted work
- `DROP TABLE employees` in a migration that was meant for a different table
- `git push --force` on main that overwrote a teammate's merge
- `rm -rf node_modules && rm package-lock.json` when `pnpm install` would have fixed the issue
