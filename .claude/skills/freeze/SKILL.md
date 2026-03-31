---
name: freeze
description: "Edit lock for Redoe OS. Restricts file edits to a specific directory — prevents agents from accidentally touching files outside their scope. Essential for parallel worktree agents from /decompose. Implement as a PreToolUse hook on Edit and Write tools."
---

# /freeze — Lock Edits to One Directory

Restricts all file edits to a single directory. Everything outside is read-only. Prevents agents from accidentally modifying shared files, other agents' work, or system configuration.

**Team:** Steve (VP), Andy (backend), Ben Wang.

## Usage

```
/freeze apps/web/src/time-tracking/    — Lock edits to this directory
/freeze supabase/migrations/           — Lock edits to migrations only
/freeze .                              — Lock edits to current directory (all project files)
/unfreeze                              — Remove the lock
/freeze --status                       — Show current freeze boundary
```

**When to use:**
- During `/decompose` parallel agent work — each agent freezes to its own scope
- When debugging production — freeze everything except the file you're investigating
- When a junior dev is working — prevent accidental edits to shared config

---

## Implementation

Add to `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/freeze-guard.sh \"$TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

### Hook Script: `.claude/hooks/freeze-guard.sh`

The hook reads the freeze boundary from `_workspace/freeze-lock.json`:

```json
{
  "active": true,
  "boundary": "apps/web/src/time-tracking/",
  "set_by": "agent-1",
  "set_at": "2026-03-30T14:00:00Z",
  "reason": "DECOMP-005 Task 1: Time tracking components"
}
```

**Logic:**
1. Read `_workspace/freeze-lock.json`
2. If `active: false` or file doesn't exist → allow all edits
3. Extract `file_path` from the tool input
4. Check if `file_path` starts with `boundary`
5. If yes → allow
6. If no → BLOCK with message

### Always Allowed (even when frozen)

These paths are never blocked, regardless of freeze boundary:

| Path | Why |
|------|-----|
| `_workspace/*.json` | Workspace state files (review-status, deploy-history, etc.) |
| `_workspace/*.md` | Workspace scratch files |
| `.claude/settings.json` | Need to modify hooks/config |
| `supabase/tests/*.sql` | Test files — agents should always be able to write tests |

---

## Alert Format

When a blocked edit is intercepted:

```
🔒 FREEZE — Edit blocked
────────────────────────────────────────────
Attempted edit:  apps/web/src/jobs/job-table.tsx
Freeze boundary: apps/web/src/time-tracking/
Reason:          DECOMP-005 Task 1 — you're scoped to time-tracking only

This file belongs to another agent's scope.
If you need changes here, add it as a dependency in your task output.

To override: /unfreeze (requires main session, not agent)
────────────────────────────────────────────
```

---

## Agent Integration

### With `/decompose`

When `/decompose` breaks work into parallel tasks, each task includes a Scope section:

```markdown
### Task 1: Time Tracking Components
**Scope:** apps/web/src/time-tracking/
**Branch:** feat/SPEC-005-task-1-time-tracking
```

The agent launcher should auto-set the freeze boundary:

```bash
# In the agent launch script
echo '{"active":true,"boundary":"apps/web/src/time-tracking/","set_by":"agent-1"}' > _workspace/freeze-lock.json
```

### With `/careful`

`/freeze` and `/careful` complement each other:
- `/careful` — blocks dangerous COMMANDS (rm -rf, force-push, DROP TABLE)
- `/freeze` — blocks edits OUTSIDE a directory boundary

Use `/guard` (informal alias) to mean: enable both `/careful` and `/freeze`.

---

## Output

### `/freeze --status`

```
=========================================
FREEZE STATUS — Redoe OS
=========================================
Active:     YES
Boundary:   apps/web/src/time-tracking/
Set by:     agent-1 (DECOMP-005 Task 1)
Set at:     2026-03-30 14:00:00 ET
Duration:   42 minutes

Allowed:
  ✓ apps/web/src/time-tracking/**  (any file)
  ✓ _workspace/**                  (always allowed)
  ✓ supabase/tests/**              (always allowed)

Blocked:
  ✗ Everything else (read-only)
=========================================
```

### `/unfreeze`

```
Freeze removed. All files are now editable.
```

---

## Anti-Patterns

- Don't freeze the entire repo (`/freeze /`) — that blocks everything including workspace files
- Don't leave freeze active after agent work completes — always `/unfreeze` in cleanup
- Don't use freeze as a substitute for proper `/decompose` scoping — freeze is a safety net, not a planning tool
- Don't freeze during `/investigate` — debugging often requires reading AND editing across boundaries
