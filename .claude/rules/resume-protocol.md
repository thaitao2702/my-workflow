---
alwaysApply: true
---

## Resume Protocol

**CLI reference:** `.claude/scripts/workflow_cli.reference.md`

When starting a session, check for interrupted work:

1. Use the CLI to find active plans
2. If found:
   - **Single plan** → use it as `$PLAN_DIR`, get the current resume point, inform the user: "Found interrupted execution: **{plan-name}** — Phase {N}, Task {M}. Resume with `/execute --resume`."
   - **Multiple plans** → list all with name and status, inform the user: "Found {count} interrupted executions:" followed by the list. Ask which to resume, or suggest `/execute --resume` to choose.
3. Do NOT auto-resume without user confirmation.

### On Session Interruption

If you detect context is running low (from context monitor warnings) or the user wants to stop:

1. Pause execution (`$PLAN_DIR` should already be set from `/execute` Step 1):
   - Use the CLI to pause execution
   - Use the CLI to log: "Session interrupted — context low / user requested"
2. Use the CLI to get the current resume point and tell the user

### Error Recovery

If a task fails during execution:

1. Use the CLI to mark the task as failed (include error description)
2. Do NOT silently skip the task
3. Ask the user: retry, skip, or abort?
4. Use the CLI to log the user's decision
