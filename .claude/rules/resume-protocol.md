---
alwaysApply: true
---

## Resume Protocol

When starting a session, check for interrupted work:

1. Run: `python .claude/scripts/workflow_cli.py find-active`
2. If found (returns a plan directory path — use this as `$PLAN_DIR`):
   - Run: `python .claude/scripts/workflow_cli.py state current --plan-dir $PLAN_DIR`
   - Inform the user: "Found interrupted execution: **{plan-name}** — Phase {N}, Task {M}. Resume with `/execute --resume`."
3. Do NOT auto-resume without user confirmation.

### On Session Interruption

If you detect context is running low (from context monitor warnings) or the user wants to stop:

1. Pause execution (`$PLAN_DIR` should already be set from `/execute` Step 1):
   ```
   python .claude/scripts/workflow_cli.py state pause --plan-dir $PLAN_DIR
   python .claude/scripts/workflow_cli.py state log "Session interrupted — context low / user requested" --plan-dir $PLAN_DIR
   ```
2. Tell the user the exact resume point:
   ```
   python .claude/scripts/workflow_cli.py state current --plan-dir $PLAN_DIR
   ```

### Error Recovery

If a task fails during execution:

1. Mark the failure:
   ```
   python .claude/scripts/workflow_cli.py state fail-task {N} {task-id} "error description" --plan-dir $PLAN_DIR
   ```
2. Do NOT silently skip the task
3. Ask the user: retry, skip, or abort?
4. Log the decision:
   ```
   python .claude/scripts/workflow_cli.py state log "Task {task-id}: user chose {decision}" --plan-dir $PLAN_DIR
   ```
