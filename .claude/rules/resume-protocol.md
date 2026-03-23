---
alwaysApply: true
---

## Resume Protocol

When starting a session, check for interrupted work:

1. Look for any `state.md` files in `.workflow/plans/` with `status: executing` or `status: paused`
2. If found, inform the user: "Found interrupted execution: **{plan-name}** — Phase {N}, Task {M}. Resume with `/execute --resume`."
3. Do NOT auto-resume without user confirmation.

### State Markers

| Marker | Meaning |
|--------|---------|
| `[x]` | Task completed |
| `[>]` | Task in progress (has sub-progress below) |
| `[ ]` | Task not started |
| `✓` | Sub-step completed |
| `○` | Sub-step next (resume point) |

### On Session Interruption

If you detect context is running low (from context monitor warnings) or the user wants to stop:

1. Save current progress to `state.md`:
   - Update `last_updated` timestamp in frontmatter
   - Mark current task with `[>]` and document sub-progress
   - Add entry to Session Log
2. Update `status` in frontmatter to `paused`
3. Tell the user the exact resume point

### Error Recovery

If a task fails during execution:

1. Mark the task with `[!]` in state.md and note the error
2. Do NOT silently skip the task
3. Ask the user: retry, skip, or abort?
4. Log the decision in Session Log
