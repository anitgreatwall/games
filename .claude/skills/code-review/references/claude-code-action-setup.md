# Claude Code Action Setup for Redoe OS

## GitHub Action Configuration

Add to `.github/workflows/claude-review.yml`:

```yaml
name: Claude Code Review

on:
  pull_request:
    branches: [main]
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: write

jobs:
  claude-review:
    name: Code Review
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: anthropics/claude-code-action@v1
        with:
          anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
          model: claude-sonnet-4-20250514
          direct_prompt: |
            Review this PR for Redoe OS using the checklist in
            .claude/skills/code-review/references/redoe-review-checklist.md

            Post a single PR comment with:
            1. Summary (2-3 sentences)
            2. Checklist results (checked/unchecked)
            3. Issues found (CRITICAL / WARNING / INFO)
            4. Security concerns
            5. Verdict: APPROVE / REQUEST CHANGES / COMMENT
          max_tokens: 4096
          allowed_tools: "Read,Bash,Glob,Grep"
```

## Required Secrets

| Secret | Where to get it |
|--------|----------------|
| `ANTHROPIC_API_KEY` | console.anthropic.com → API Keys |

## Cost Management

- Uses Sonnet (not Opus) — ~$0.15 per review
- `max_tokens: 4096` caps response length
- `timeout-minutes: 10` prevents runaway
- Advisory only — does NOT block merge

## First-Time Setup

1. Create the secret in GitHub: Settings → Secrets → Actions → New
2. Add the workflow file to `.github/workflows/`
3. Open a test PR to verify it posts a comment
4. Adjust the prompt based on initial results

## Troubleshooting

- **No comment posted:** Check that `permissions: pull-requests: write` is set
- **Review too generic:** Add more specific context to the prompt (file paths, business rules)
- **Too expensive:** Switch to Haiku for non-critical PRs, keep Sonnet for supabase/ changes
