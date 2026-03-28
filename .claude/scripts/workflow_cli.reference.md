# Workflow CLI Reference

**Script:** `python .claude/scripts/workflow_cli.py`
**Global flag:** `--plan-dir DIR` — required on all commands except `find-active` and `init`. Without it, CLI auto-resolves to latest plan alphabetically, which silently targets the wrong plan when multiple exist.

## Commands by Role

### Orchestrator — Plan Reading

| Command | Purpose | Output |
|---------|---------|--------|
| `plan get --plan-dir $PLAN_DIR` | Full plan JSON | JSON object with name, status, summary, scope, phases, risks, etc. |
| `plan get FIELD --plan-dir $PLAN_DIR` | Single field from plan | Raw field value (string for text fields, JSON for objects/arrays) |
| `plan phases --plan-dir $PLAN_DIR` | List all phases | One JSON object per line: `{"phase": N, "name": "...", "group": "A", "status": "..."}` |
| `plan show --plan-dir $PLAN_DIR` | Human-readable plan summary | Formatted text with phase list, task counts, status |
| `plan set-status STATUS --plan-dir $PLAN_DIR` | Update plan status | Sets status: `draft` → `reviewed` → `approved` → `executing` → `completed` |

### Orchestrator — Phase Reading

| Command | Purpose | Output |
|---------|---------|--------|
| `phase show N --plan-dir $PLAN_DIR` | Full phase JSON | JSON object with phase number, name, goal, tasks array, etc. |
| `phase tasks N --plan-dir $PLAN_DIR` | All tasks in a phase | JSON array of task objects (id, name, description, files, acceptance_criteria, test_requirements) |
| `phase task N TASK_ID --plan-dir $PLAN_DIR` | Single task detail | JSON object for one task |

### Orchestrator — Execution State

| Command | Purpose | Output |
|---------|---------|--------|
| `state show --plan-dir $PLAN_DIR` | Human-readable execution status | Formatted tree: phases, tasks, checkmarks, session log |
| `state current --plan-dir $PLAN_DIR` | Machine-readable resume point | JSON: `{"plan": "...", "status": "...", "current_phase": N, "current_task": "task-id", "execution_start_commit": "..."}` |
| `state get FIELD --plan-dir $PLAN_DIR` | Single field from state | Raw field value (e.g., `state get execution_start_commit`) |
| `state start-execution COMMIT --plan-dir $PLAN_DIR` | Begin execution | Records start commit hash and sets status to `executing` |
| `state start-phase N --plan-dir $PLAN_DIR` | Mark phase in-progress | Sets phase status to `in_progress`, records current_phase |
| `state complete-phase N --plan-dir $PLAN_DIR` | Mark phase done | Sets phase status to `completed` |
| `state complete --plan-dir $PLAN_DIR` | Mark entire execution done | Sets plan status to `completed` |
| `state pause --plan-dir $PLAN_DIR` | Pause execution | Sets status to `paused` — used on session interruption |
| `state log MESSAGE --plan-dir $PLAN_DIR` | Append to session log | Timestamped entry in log array |

### Executor — Task Progress (used by executor subagent)

| Command | Purpose | When |
|---------|---------|------|
| `state set-active N TASK_ID --plan-dir $PLAN_DIR` | Mark task as in-progress | Before starting each task |
| `state complete-task N TASK_ID --plan-dir $PLAN_DIR` | Mark task as done | After task passes tests |
| `state fail-task N TASK_ID REASON --plan-dir $PLAN_DIR` | Mark task as failed | When task hits a blocker |
| `state skip-task N TASK_ID REASON --plan-dir $PLAN_DIR` | Mark task as skipped | When user approves skipping |
| `state substep N TASK_ID STEP done\|next --plan-dir $PLAN_DIR` | Track substep progress | Optional fine-grained tracking within a task |

### Discovery

| Command | Purpose | Output |
|---------|---------|--------|
| `find-active` | Find plan with active/paused execution | Absolute path to plan directory, or empty if none |
| `init PLAN_DIR` | Initialize state.json from plan files | Creates `state.json` with correct structure. **Must run after plan approval.** |

## Status Lifecycles

**Plan:** `draft` → `reviewed` → `approved` → `executing` → `completed`
**Phase:** `pending` → `in_progress` → `completed`
**Task:** `pending` → `active` → `completed` | `failed` | `skipped`
**Execution:** `not_started` → `executing` → `paused` → `executing` → `completed`
