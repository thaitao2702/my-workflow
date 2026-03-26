---
description: "Execute an approved plan — phase-by-phase with TDD, reviews, state tracking, and doc updates"
---

# /execute — Execute Plan

You are executing an approved plan phase-by-phase. Track state, enforce TDD, run reviews, maintain codebase knowledge.

**CLI shorthand:** `python .claude/scripts/workflow_cli.py` (all state/plan/phase reads and writes go through this CLI)

**CRITICAL: Every CLI command MUST include `--plan-dir $PLAN_DIR`.** Without it, the CLI auto-resolves to the latest plan alphabetically, which silently targets the wrong plan when multiple plans exist.

**Input:** `/execute` (uses latest approved plan), `/execute {plan-path}`, or `/execute --resume`
**Output:** Implemented code, updated state, reviewed and documented

## Step 1: Load Plan

### Step 1a: Resolve PLAN_DIR

Determine `$PLAN_DIR` from the user's input. **This must happen first — all subsequent CLI calls use it.**

| Argument | Action |
|----------|--------|
| `--resume` | Run `python .claude/scripts/workflow_cli.py find-active` → use the output path as `$PLAN_DIR` |
| Path ending in `.json` (e.g., `plans/260325-foo/plan.json`) | Strip the filename: use the parent directory as `$PLAN_DIR` |
| Path to a directory | Use as-is as `$PLAN_DIR` |
| No argument | Let CLI auto-resolve: run `python .claude/scripts/workflow_cli.py plan get --plan-dir` without a value will error — instead, list available plans and ask user to confirm which one |

After resolving, **confirm to the user:** "Using plan directory: `$PLAN_DIR`"

### Step 1b: Read Plan

```
python .claude/scripts/workflow_cli.py plan get --plan-dir $PLAN_DIR
python .claude/scripts/workflow_cli.py plan phases --plan-dir $PLAN_DIR
```

Determine which group to execute next (from the phases list + state).

Read project overview: `.workflow/project-overview.md`

### Step 1c: Start or Resume

If NOT resuming — record execution start:
```
python .claude/scripts/workflow_cli.py state start-execution $(git rev-parse HEAD) --plan-dir $PLAN_DIR
```

If resuming — get the resume point:
```
python .claude/scripts/workflow_cli.py state current --plan-dir $PLAN_DIR
```
This returns the current phase, task, and any substep progress. Continue from there.

## Step 2: Execute Groups

Process groups sequentially (A → B → C). Within each group, phases can run in parallel.

### For each group:

#### Step 2a: Phase Start

1. Mark phase as in progress:
   ```
   python .claude/scripts/workflow_cli.py state start-phase {N} --plan-dir $PLAN_DIR
   ```
2. Read phase tasks:
   ```
   python .claude/scripts/workflow_cli.py phase tasks {N} --plan-dir $PLAN_DIR
   ```
3. Load relevant `.analysis.md` files (Level 1: frontmatter + CONTENT)
   - These should exist from planning. If missing → use the Skill tool to invoke `/analyze` as fallback
4. Prepare executor context

#### Step 2b: Task Execution

For each task in the phase:

1. Mark task as active:
   ```
   python .claude/scripts/workflow_cli.py state set-active {N} {task-id} --plan-dir $PLAN_DIR
   ```
2. Read task details:
   ```
   python .claude/scripts/workflow_cli.py phase task {N} {task-id} --plan-dir $PLAN_DIR
   ```
3. Spawn a subagent with `.claude/agents/executor.md`. Provide:
   - **Task description + acceptance criteria** from the phase task data
   - **Project overview** — `.workflow/project-overview.md`
   - **Component analysis docs** — relevant `.analysis.md` files
   - **Code quality rules** — read all files in `.workflow/rules/code/` (if any exist)
   - **TDD policy** — from `.claude/rules/tdd-policy.md`

4. Track substep progress as the executor works:
   ```
   python .claude/scripts/workflow_cli.py state substep {N} {task-id} "Test written" done --plan-dir $PLAN_DIR
   python .claude/scripts/workflow_cli.py state substep {N} {task-id} "Implementation" next --plan-dir $PLAN_DIR
   ```

5. When task completes:
   ```
   python .claude/scripts/workflow_cli.py state complete-task {N} {task-id} --plan-dir $PLAN_DIR
   ```

#### Step 2c: Phase Review

After all tasks in a phase complete, spawn a subagent with `.claude/agents/reviewer.md`.

Provide:
1. **All code changes** from this phase (git diff)
2. **Code quality rules** — `.workflow/rules/code/*.md`
3. **Phase acceptance criteria** — from the phase task data (already loaded in Step 2b)
4. **Component docs** — `.analysis.md` files for affected components

Review checks:
- All acceptance criteria met
- No scope creep
- Tests cover requirements
- General quality rules (`.claude/rules/quality-criteria.md`)
- Project-specific code rules

If **FAIL**: executor agent fixes issues (max 2 fix rounds). If still failing after 2 rounds, pause and ask user.

Present review to user for approval before proceeding.

#### Step 2d: Playwright Check (conditional)

Only if the phase has `affected_components` that include UI components AND `.workflow/config.json` has `playwright_check: true`:
- Run Playwright to navigate affected pages
- Check: page loads, no console errors
- Report to user

#### Step 2e: Phase Completion

1. Mark phase completed:
   ```
   python .claude/scripts/workflow_cli.py state complete-phase {N} --plan-dir $PLAN_DIR
   ```
2. Run regression: tests from all prior completed phases still pass
3. Proceed to next group

**Note:** Documentation updates are NOT done per-phase. They happen once in the final reconciliation (Step 3) after all phases complete.

## Step 3: Final Reconciliation (Documentation Update)

After ALL phases complete, this is the **single point** where documentation gets updated.

### Step 3a: Identify All Changed Components

1. Get the execution start commit:
   ```
   python .claude/scripts/workflow_cli.py state get execution_start_commit --plan-dir $PLAN_DIR
   ```
2. Get the full diff since execution started: `git diff {start_commit}..HEAD --name-only`
3. From the changed files, identify which components were affected
4. Also read affected components from phase files — deduplicate

### Step 3b: Assess and Update Each Component

For each affected component, use the Skill tool to invoke `/doc-update`.

Provide:
- The component path
- The full git diff: `git diff {start_commit}..HEAD -- {component_files}`
- Plan context:
  ```
  python .claude/scripts/workflow_cli.py plan get summary --plan-dir $PLAN_DIR
  ```

### Step 3c: Verify Project Overview

1. Check if changes affect project architecture, modules, or data model
2. If yes: update `.workflow/project-overview.md`
3. If no: skip

### Step 3d: Post-Execution Reflection

Reflect on what was learned during execution. **Skip this step entirely if nothing significant was discovered.**

This is the most valuable reflection point — execution is where rubber meets road. The gap between "what was planned" and "what actually happened" produces the richest corrections.

**What to look for:**

During task execution, the executor agents may have encountered:
- **Component behaviors not in the analysis docs** — "authService.validate() throws on expired tokens but returns false on invalid tokens. This wasn't in the Hidden Details."
- **Plan assumptions that turned out wrong** — "The plan assumed the API supports batch operations, but it only supports single-item calls. I had to implement a loop."
- **Undocumented dependencies or side effects** — "Updating the user profile also invalidates the session cache. Not documented anywhere."
- **Conventions or patterns that differ from what project-overview described** — "The overview says services use repository pattern, but the payments module uses direct DB queries."

**What to do:**

Only for **non-trivial findings** that could cause real problems in future work:

1. Present each finding to the user:
   - "During execution, I discovered: {finding}"
   - "This should be documented in: {target document}"
   - "Proposed update: {specific content to add/change}"
2. If user agrees: apply the update:
   - Component behavior → update `.analysis.md` Hidden Details table
   - Wrong plan assumption (repeatable) → add rule to `.workflow/rules/planning/`
   - Code pattern correction → add/update rule in `.workflow/rules/code/`
   - Architecture/overview inaccuracy → update `.workflow/project-overview.md`
3. If user disagrees or finding is trivial: skip it.

**Skip criteria:** Don't surface findings that are:
- Already captured by the `/doc-update` step (Step 3b handled it)
- Trivial — typos, minor style differences, obvious things
- One-off situations with no future relevance
- Things the user explicitly told you during execution (they already know)

### Step 3e: Template Suggestion

Assess whether the completed work represents a **repeatable pattern**:
- Did this plan create something that will likely be built again with variations?
- Are there already similar components in the codebase that followed the same shape?
- Did the task structure (phases/tasks) reveal a reusable workflow?

If yes, suggest: "This looks like a repeatable pattern ({reason}). Want to create a template now? The full execution context (decisions, discoveries, reasoning) is still fresh — this produces the richest template."

If user agrees: use the Skill tool to invoke `/template-create` with `--from-session` flag.

Pass to the template-extractor agent:
1. **Plan summary** — what was built and why
2. **Component intelligence** — from plan + analysis docs
3. **Phase/task structure** — how work was decomposed
4. **Git diff** — `git diff {execution_start_commit}..HEAD`
5. **Execution discoveries** — from Step 3d reflection (wrong assumptions, hidden behaviors)
6. **Key decisions during execution** — what the executor adapted and why

If user declines: fine. They can run `/template-create` later.

### Step 3f: Final Verification

1. Run full test suite
2. Mark execution complete:
   ```
   python .claude/scripts/workflow_cli.py state complete --plan-dir $PLAN_DIR
   ```
3. Display final progress:
   ```
   python .claude/scripts/workflow_cli.py state show --plan-dir $PLAN_DIR
   ```
4. Present execution summary to user

## Resume Protocol

When resuming an interrupted session:

1. Find the active plan:
   ```
   python .claude/scripts/workflow_cli.py find-active
   ```
   Use the output as `$PLAN_DIR`.
2. Get resume point:
   ```
   python .claude/scripts/workflow_cli.py state current --plan-dir $PLAN_DIR
   ```
   Returns: `{"current_phase": 2, "current_task": "task-03", "substeps": [...]}`
3. Determine resume point from the response:
   - If substeps exist with `"next"` status → continue from that substep
   - If current_task exists → continue from that task
   - If current_phase exists → continue from that phase
4. Tell user: "Resuming from Phase {N}, Task {M}: {description}"
5. Continue execution from that point

## Parallel Execution

When a group has multiple phases:
- Launch each phase as a separate Agent (background if possible)
- Each agent uses CLI with `--plan-dir $PLAN_DIR` to update its own phase's state
- Wait for all phases in the group to complete
- Run regression tests after the entire group finishes
- Documentation updates happen in Step 3, NOT here

## Error Handling

### Task Failure (tests won't pass, implementation blocked)
1. Mark task as failed:
   ```
   python .claude/scripts/workflow_cli.py state fail-task {N} {task-id} "reason" --plan-dir $PLAN_DIR
   ```
2. Log the error:
   ```
   python .claude/scripts/workflow_cli.py state log "Task {task-id} failed: reason" --plan-dir $PLAN_DIR
   ```
3. Ask user: **retry**, **skip**, or **abort**
4. If retry: attempt again with different approach (max 2 retries)
5. If skip:
   ```
   python .claude/scripts/workflow_cli.py state skip-task {N} {task-id} "reason" --plan-dir $PLAN_DIR
   ```
6. If abort:
   ```
   python .claude/scripts/workflow_cli.py state pause --plan-dir $PLAN_DIR
   ```

### Agent Crash (subagent fails to return)
1. Log the failure:
   ```
   python .claude/scripts/workflow_cli.py state log "Agent crash during {task-id}" --plan-dir $PLAN_DIR
   ```
2. Check: did the agent produce any partial output?
3. Retry with fresh agent spawn (max 1 retry)
4. If still failing: escalate to user

### Test Regression (prior tests break)
1. Identify which prior phase's tests broke
2. Check git diff: did current phase's code cause it?
3. If yes: fix before proceeding
4. If unclear: report to user

### Review Loop (2 rounds failed)
1. After 2 failed fix rounds, do NOT keep iterating
2. Present review findings to user
3. Ask: fix manually, provide guidance, or skip review

## Constraints
- Do NOT skip TDD unless the task falls under a documented exception
- Do NOT proceed past a FAILED review without fixing issues or getting user approval
- Do NOT modify files outside the plan's scope (no scope creep)
- Do NOT read or edit state.json directly — always use the CLI
- Do NOT run any CLI command without `--plan-dir $PLAN_DIR`
- Do NOT update documentation per-phase — all doc updates happen in Step 3
- Do NOT skip the final reconciliation step
- Max 2 fix rounds per review failure — escalate to user after that
