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
| `plan review-dump --plan-dir $PLAN_DIR` | All plan data in AI-agent-friendly format | Plan overview + all phases inline + cross-reference tables (file ownership, requirement trace, acceptance spec trace) + planning rules. Single call replaces `plan get` + `plan phases` + N × `phase show`. |

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

### Orchestrator — Knowledge Persistence

| Command | Purpose | Output |
|---------|---------|--------|
| `state add-discovery PHASE_N COMPONENT WHAT WHY RISK TEST CATEGORY --plan-dir $PLAN_DIR` | Persist an executor discovery | JSON confirmation. Categories: `hidden_behavior`, `wrong_assumption`, `edge_case`, `integration_gotcha` |
| `state add-decision PHASE_N COMPONENT DECISION REASONING ALTERNATIVES --plan-dir $PLAN_DIR` | Persist an executor decision | JSON confirmation |
| `state get-discoveries --plan-dir $PLAN_DIR` | Get all persisted discoveries | JSON array of discovery objects |
| `state get-decisions --plan-dir $PLAN_DIR` | Get all persisted decisions | JSON array of decision objects |

### Discovery

| Command | Purpose | Output |
|---------|---------|--------|
| `find-active` | Find all plans with active/paused execution | One absolute path per line (newest first), or error if none |
| `init PLAN_DIR` | Initialize state.json from plan files | Creates `state.json` with correct structure. **Must run after plan approval.** |

### Analysis

| Command | Purpose | Output |
|---------|---------|--------|
| `analysis check COMPONENT [--recursive]` | Check if analysis doc is fresh, stale, or missing | JSON: `{"status": "fresh\|stale\|missing", "analysis_path": "...", "reason?": "...", "changed_deps?": [...]}` |
| `analysis read COMPONENT [--level 0\|1\|2]` | Read analysis doc at progressive loading level | Extracted content. Level 0: frontmatter, Level 1 (default): frontmatter + CONTENT, Level 2: full |
| `analysis list DIR` | Find all `.analysis.md` files recursively in a directory | One relative path per line |

### Batch Operations

| Command | Purpose | Output |
|---------|---------|--------|
| `batch --commands 'JSON_ARRAY'` | Execute multiple CLI sub-commands in one call | Sectioned output: `══ [N/total] {command} ══` per result |
| `read FILE [FILE:start-end ...]` | Read one or more files | Sectioned: `══ FILE: {path} ══` per file. Handles binary detection, missing files. |
| `grep [--path P] [--type T] [--context N] PATTERN` | Search for regex pattern in files | ripgrep output, or `(no matches)` if none found |

**When to use batch:** When you need results from 3+ independent commands and know all inputs upfront. Each element in the JSON array is a sub-command string using the same syntax as standalone CLI calls.

**Batch output format:**
```
══ [1/N] {command_string} ══
{command output}

══ [2/N] {command_string} ══
{command output}
```

Errors per sub-command show `ERROR: {message}` without aborting the batch.

**Example:**
```
batch --commands '["read src/foo.ts src/bar.ts", "grep --path src/ --type ts class AuthService", "analysis check src/services/auth.ts"]'
```

### Utility

| Command | Purpose | Output |
|---------|---------|--------|
| `hash FILE [FILE...]` | SHA-256 content hash of file(s) | Hex digest. Multiple files are sorted by path and concatenated before hashing. |

### Configuration

| Command | Purpose | Output |
|---------|---------|--------|
| `config get` | Full config JSON | JSON object from `.workflow/config.json`, or `{}` if file missing |
| `config get FIELD` | Single config field | JSON value, or `null` if field or file missing |

Config fields: `test_command` (string — test runner command), `test_command_timeout` (ms, default 120000), `playwright_check` (boolean), `acceptance_mode` (`"auto"` | `"test"` | `"reason"`, default `"auto"`).

## Status Lifecycles

**Plan:** `draft` → `reviewed` → `approved` → `executing` → `completed`
**Phase:** `pending` → `in_progress` → `completed`
**Task:** `pending` → `active` → `completed` | `failed` | `skipped`
**Execution:** `not_started` → `executing` → `paused` → `executing` → `completed`
