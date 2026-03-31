---
name: verify
description: Verify task completion by auditing a manifest against actual outputs. Use after any exhaustive task or batch of agents completes.
user_invocable: true
---

# /verify — Task Completion Verification

## Purpose
Independent audit of whether an exhaustive task actually completed. Checks the manifest (source of truth) against actual outputs. No incentive to rationalize — just count and report.

## Trigger
- User invokes `/verify`
- After any batch of agents completes on an exhaustive task
- Before reporting any task as "done"

## Steps

1. **Find the active manifest.** Search for `_workspace/manifest.md` in the current project directory. If no manifest exists, report: "No manifest found. Either this isn't an exhaustive task or the manifest wasn't created."

2. **Count checkboxes.**
   - Total items: count all `- [ ]` and `- [x]` lines
   - Done items: count `- [x]` lines
   - Remaining: Total - Done

3. **Cross-reference outputs.** For each checked item:
   - Verify the corresponding output file or vault entry exists
   - Flag any items marked done but with no detectable output ("phantom completions")

4. **Report.**
   ```
   ## Verification Report
   - Manifest: [path]
   - Status: [IN_PROGRESS | COMPLETE | PAUSED]
   - Items: X/Y verified (Z remaining)
   - Phantom completions: [count] (marked done but no output found)
   - Verdict: [PASS | FAIL — N items need attention]
   ```

5. **If FAIL:** List the specific unchecked or phantom items. Recommend batch size for follow-up agents.

## Rules
- Do NOT update the manifest yourself — just report. The orchestrating agent handles remediation.
- Do NOT rationalize gaps. If 30 items are unchecked, say "30 items unchecked" — don't say "most items are done."
- This skill should take <30 seconds. Read the manifest, count, report. No deep analysis needed.
