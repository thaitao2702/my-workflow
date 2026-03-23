---
description: "Execute an approved plan — phase-by-phase with TDD, reviews, state tracking, and doc updates"
---

# /execute — Execute Plan

You are executing an approved plan phase-by-phase. Track state, enforce TDD, run reviews, maintain codebase knowledge.

**Input:** `/execute` (uses latest approved plan), `/execute {plan-path}`, or `/execute --resume`
**Output:** Implemented code, updated state, reviewed and documented

## Step 1: Load Plan

1. If `--resume`: read `.workflow/plans/` to find the plan with `status: executing` in its `state.md`
2. If path provided: read the specified plan directory
3. If no argument: find the most recent plan directory in `.workflow/plans/` with `status: approved`
4. Read: `plan.md`, all `phase-NN-*.md` files, `state.md`
5. Read: `.workflow/project-overview.md`
6. Determine: which group to execute next (from dependency graph in plan.md)
7. If resuming: find `[>]` marker in state.md body, continue from there

## Step 2: Execute Groups

Process groups sequentially (A → B → C). Within each group, phases can run in parallel.

### For each group:

#### Step 2a: Phase Start
1. Update `state.md`: phase status → `[IN PROGRESS]`
2. Read phase file to get affected components
3. Load relevant `.analysis.md` files (Level 1: frontmatter + CONTENT)
   - These should exist from planning. If missing → use the Skill tool to invoke `/analyze` as fallback
4. Prepare executor context

#### Step 2b: Task Execution

For each task in the phase, spawn a subagent with `.claude/agents/executor.md`.

Provide the agent with:
1. **Task description + acceptance criteria** from the phase file
2. **Project overview** — `.workflow/project-overview.md`
3. **Component analysis docs** — relevant `.analysis.md` files
4. **Code quality rules** — read all files in `.workflow/rules/code/` (if any exist)
5. **Source files** being modified (agent reads these)
6. **TDD policy** — from `.claude/rules/tdd-policy.md`

The executor agent:
1. Writes failing tests first (unless TDD exception applies)
2. Implements code to pass tests
3. Runs tests to confirm pass
4. Returns the result

After each task completes, **update state.md**:
- Mark task `[x]` with ✓
- If task in progress: use `[>]` marker with sub-progress bullets
- Update `current_task` in frontmatter
- Update `last_updated` timestamp

#### Step 2c: Phase Review

After all tasks in a phase complete, spawn a subagent with `.claude/agents/reviewer.md`.

Provide:
1. **All code changes** from this phase (git diff)
2. **Code quality rules** — `.workflow/rules/code/*.md`
3. **Phase acceptance criteria** — from the phase file
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

#### Step 2e: Documentation Update

Use the Skill tool to invoke `/doc-update` with the list of affected components and the git diff for this phase.

#### Step 2f: Phase Completion

1. Update `state.md`: phase status → `[COMPLETED]`
2. Run regression: tests from all prior completed phases still pass
3. Add entry to Session Log in state.md
4. Proceed to next group

## Step 3: Final Reconciliation

After ALL phases complete:

1. Read all modified files across all phases
2. For each affected component: run staleness check on its `.analysis.md`
   - If stale: use the Skill tool to invoke `/doc-update`
3. Verify `.workflow/project-overview.md` still accurate (update if modules/architecture changed)
4. Run full test suite
5. Update `state.md`: status → `completed`
6. Generate execution summary:
   - Phases completed, tasks completed
   - Test results
   - Review results
   - Doc updates performed
7. Present summary to user

## Resume Protocol

When resuming an interrupted session:

1. Read `state.md` frontmatter → `current_phase`, `current_task`, `status`
2. Find `[>]` marker in body → get sub-progress
3. Determine resume point:
   - Mid-task (has `○` markers): continue from the next `○` item
   - Between tasks: start next `[ ]` task
   - Between phases: start next `[PENDING]` phase
4. Tell user: "Resuming from Phase {N}, Task {M}: {description}"
5. Continue execution from that point

## Parallel Execution

When a group has multiple phases:
- Launch each phase as a separate Agent (background if possible)
- Each agent updates its own section of state.md
- Wait for all phases in the group to complete
- Run regression tests after the entire group finishes

## Error Handling

### Task Failure (tests won't pass, implementation blocked)
1. Mark task as `[!]` in state.md with error description
2. Add error to Session Log with timestamp
3. Ask user: **retry** (try again), **skip** (mark skipped, continue), or **abort** (pause execution)
4. If retry: attempt the task again with a different approach (max 2 retries)
5. If skip: mark `[S]` in state.md, note the skip reason, continue to next task
6. If abort: set status to `paused`, save full state, report to user

### Agent Crash (subagent fails to return)
1. Log the failure in Session Log
2. Check: did the agent produce any partial output (files written)?
3. If partial: assess whether partial work is usable or needs rollback
4. Retry the task with a fresh agent spawn (max 1 retry)
5. If still failing: escalate to user

### Test Regression (prior tests break)
1. Identify which prior phase's tests broke
2. Check git diff: did current phase's code cause it?
3. If yes: fix before proceeding (this is a real bug)
4. If unclear: report to user with the failing test and diff context

### Review Loop (2 rounds failed)
1. After 2 failed fix rounds, do NOT keep iterating
2. Present the review findings to the user
3. Ask: fix manually, provide guidance, or skip review

## Constraints
- Do NOT skip TDD unless the task falls under a documented exception
- Do NOT proceed past a FAILED review without fixing issues or getting user approval
- Do NOT modify files outside the plan's scope (no scope creep)
- Do NOT forget to update state.md after every task — this is the resume lifeline
- Do NOT skip the final reconciliation step
- Max 2 fix rounds per review failure — escalate to user after that
