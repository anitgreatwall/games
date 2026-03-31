# Claude Code Threat Patterns — Security Reference

> Source: Community threat research (Claude Code Ultimate Guide threat database, 2026)
> Last updated: 2026-03-30
> Used by: `/security-audit` Step 6 (Claude Code self-security check)

## Category 1: Malicious Skills

Skills (SKILL.md files) can contain hidden instructions that override Claude's behavior.

| Pattern | Risk | Detection |
|---------|------|-----------|
| **Prompt injection in SKILL.md** | Skill description contains instructions that override project rules (e.g., "ignore previous instructions") | Grep SKILL.md files for override/ignore/forget patterns |
| **Data exfiltration via tool_use** | Skill instructs Claude to send codebase content to external URLs (fetch/curl to unknown domains) | Grep skills for URLs not in project whitelist |
| **Permission escalation** | Skill adds overly permissive Bash allow rules (e.g., `Bash(*)`, `Bash(rm:*)`) | Check settings.json allow list for wildcard patterns |
| **Hidden file writes** | Skill writes files outside declared scope (e.g., modifies .env, settings.json) | Audit skill's declared vs actual file access |
| **Dependency injection** | Skill installs packages not needed for its function | Check for npm install/pip install in skill execution |

## Category 2: Configuration Vulnerabilities

| Pattern | Risk | Detection |
|---------|------|-----------|
| **Overly permissive allow rules** | `settings.json` allows destructive commands (rm -rf, git push --force) | Parse allow list for high-risk command patterns |
| **Missing deny rules** | No explicit blocks on `git push --force`, `git reset --hard`, `.env` access | Verify deny list covers destructive operations |
| **Hooks tampering** | PostCompact or other hooks modified to inject instructions | Hash-check hook content against known-good state |
| **Env var leakage** | `CLAUDE_CODE_*` env vars expose project structure or keys | Check env block in settings.json for sensitive values |
| **MCP server trust** | Untrusted MCP servers with broad tool access | Audit mcpServers config for unknown servers |

## Category 3: Supply Chain

| Pattern | Risk | Detection |
|---------|------|-----------|
| **Typosquatted skills** | Skill names similar to popular skills but with malicious content | Compare installed skill names against known-good list |
| **Unvetted community skills** | Skills from unknown sources without code review | Check skill authorship and review status |
| **MCP dependency confusion** | MCP server pulls from untrusted npm/pip packages | Audit MCP server package.json for suspicious deps |
| **Stale dependencies in MCP** | MCP servers with known CVEs in their dependencies | Run audit on MCP server dependencies |

## Category 4: Runtime Threats

| Pattern | Risk | Detection |
|---------|------|-----------|
| **Context window poisoning** | Tool results contain prompt injection attempts | Flag suspicious patterns in tool output |
| **Memory file manipulation** | Adversary modifies MEMORY.md to inject persistent false instructions | Hash-check memory files, verify authorship |
| **Plan file manipulation** | Plan files contain hidden instructions beyond the stated plan | Review plan files for instruction-like content |
| **Webhook exfiltration** | Hooks configured to POST data to external endpoints | Grep hook commands for curl/fetch/wget to external URLs |

## Redoe OS Specific Checks

| Check | What to verify |
|-------|---------------|
| **settings.json permissions** | deny list includes: `git push --force`, `git reset --hard`, `git clean`, `.env` read/write |
| **Skills directory integrity** | All files in `.claude/skills/` are known/reviewed (no unexpected additions) |
| **Hook safety** | All hooks in settings.json use safe commands (no network calls, no file destruction) |
| **MCP server count** | No unexpected MCP servers configured (Redoe OS currently uses zero) |
| **Memory file review** | Memory files contain only project-relevant information, no instruction overrides |
