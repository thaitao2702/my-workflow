---
description: "Execute an approved plan — phase-by-phase with TDD, reviews, state tracking, and doc updates"
---

# /execute — Execute Plan

You are executing an approved plan phase-by-phase. Track state, enforce TDD, run reviews, maintain codebase knowledge.

**CLI reference:** `.claude/scripts/workflow_cli.reference.md` — use for all plan/phase/state operations. Read it to find exact command syntax.

**CRITICAL: Every CLI command MUST include `--plan-dir $PLAN_DIR`.** Without it, the CLI auto-resolves to the latest plan alphabetically, which silently targets the wrong plan when multiple plans exist.

**Input:** `/execute` (uses latest approved plan), `/execute {plan-path}`, or `/execute --resume`
**Output:** Implemented code, updated state, reviewed and documented

## Step 1: Load Plan

### Step 1a: Resolve PLAN_DIR

Determine `$PLAN_DIR` from the user's input. **This must happen first — all subsequent CLI calls use it.**

| Argument | Action |
|----------|--------|
| `--resume` | Use the CLI to find active plans. If one result → use it as `$PLAN_DIR`. If multiple results → present the list to the user and ask which plan to resume. Show each plan's name and current phase/task for context. |
| Path ending in `.json` (e.g., `plans/260325-foo/plan.json`) | Strip the filename: use the parent directory as `$PLAN_DIR` |
| Path to a directory | Use as-is as `$PLAN_DIR` |
| No argument | List available plans in `.workflow/plans/` and ask user to confirm which one |

After resolving, **confirm to the user:** "Using plan directory: `$PLAN_DIR`"

### Step 1b: Read Plan

Use the CLI to read the full plan JSON and list all phases. Determine which group to execute next (from the phases list + state).

Read project overview: `.workflow/project-overview.md`

### Step 1c: Start or Resume

If NOT resuming — use the CLI to record execution start with the current git commit hash (`git rev-parse HEAD`).

If resuming — use the CLI to get the current resume point. This returns the current phase, task, and any substep progress. Continue from there.

## Step 2: Execute Groups

Process groups sequentially (A → B → C). Within each group, phases can run in parallel.

### For each group:

#### Step 2a: Phase Start + Analysis Gate

1. Use the CLI to mark the phase as in-progress
2. Use the CLI to read all tasks for the phase
3. **Analysis gate:** For each component the phase touches (`affected_components` in phase JSON), use the CLI `analysis check --recursive` command:
   - **`fresh`** → use the CLI `analysis read --level 1` command to get the analysis content for the executor prompt
   - **`stale`** → use the Skill tool to invoke `/analyze {component-path} --recursive`, then read the fresh doc
   - **`missing`** → use the Skill tool to invoke `/analyze {component-path} --recursive`
4. After all analysis docs are confirmed current: collect them for the executor prompt

#### Step 2b: Phase Execution

Read the prompt template: `.claude/skills/execute/executor-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions
3. Spawn **one** executor subagent (`.claude/agents/executor.md`) for the entire phase, passing the filled **For Subagent** section as the prompt. The executor implements all tasks sequentially, tracking completion via CLI as it goes.

**Parse executor output** per `executor-prompt.md` § "For Orchestrator — Expected Output":
- Read `## Status` → `**Result**`: if `FAILURE` or `PARTIAL`, check `## Escalations` for blockers before proceeding
- Extract `## Discoveries` table rows → store for Step 3 reconciliation
- Read `## Result` → `**Files Changed**` for the reviewer, `**Tests Written/Passing**` for verification

The executor handles task-level state tracking internally:
- Marks each task active before starting it
- Marks each task complete when done
- If it hits a blocker, it stops and reports — the orchestrator handles error recovery

**Why per-phase, not per-task:** Each subagent spawn costs ~4000 tokens of context. A 4-task phase costs 16,000 tokens with per-task spawning vs 4,000 tokens per-phase. The executor also builds naturally on its own work — no re-reading files it just created.

#### Step 2c: Phase Review

After the executor returns, read the prompt template: `.claude/skills/execute/reviewer-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions and review dimensions
3. Spawn a **reviewer subagent** (`.claude/agents/reviewer.md`), passing the filled **For Subagent** section as the prompt — one-shot, fresh spawn

**Parse reviewer output** per `reviewer-prompt.md` § "For Orchestrator — Expected Output":
- Read `## Status` → `**Result**`: `PASS` or `FAIL`
- If `FAIL`: read `**Failed Dimensions**` for the list, then extract each failed dimension's `**Fix Required**` from `## Dimensions`

If **FAIL**: fix the issues yourself (you have full plan context from Step 1), then re-spawn the reviewer to verify (max 2 fix rounds). If still failing after 2 rounds, present findings to user and ask how to proceed.

Present review to user for approval before proceeding.

#### Step 2d: Playwright Check (conditional)

Only if the phase has `affected_components` that include UI components AND `.workflow/config.json` has `playwright_check: true`:
- Run Playwright to navigate affected pages
- Check: page loads, no console errors
- Report to user

#### Step 2e: Phase Completion

1. Use the CLI to mark the phase as completed
2. Proceed to next group

**Note:** Documentation updates are NOT done per-phase. They happen once in the final reconciliation (Step 3) after all phases complete.

## Step 3: Final Reconciliation

After ALL phases complete.

### Step 3a: Knowledge Layer Update

Use the Skill tool to invoke `/doc-update` (no arguments). Doc-update auto-detects the active plan via CLI and uses the conversation context — which already contains plan summary, executor discoveries, and phase results — for the full reconciliation.

### Step 3b: Completion

1. Use the CLI to mark the entire execution as complete
2. Use the CLI to display the final execution progress
3. Present execution summary to user

## Resume Protocol

When resuming an interrupted session:

1. Use the CLI to find the active plan → use the output as `$PLAN_DIR`
2. Use the CLI to get the current resume point (returns current phase, task, substeps)
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
1. Use the CLI to mark the task as failed (include reason)
2. Use the CLI to log the error
3. Ask user: **retry**, **skip**, or **abort**
4. If retry: attempt again with different approach (max 2 retries)
5. If skip: use the CLI to mark the task as skipped (include reason)
6. If abort: use the CLI to pause execution

### Executor Crash (subagent fails mid-phase)
1. Use the CLI to log the crash
2. Use the CLI to check which tasks completed (the executor tracks via CLI)
3. Re-spawn a fresh executor for the **remaining tasks only** — tell it to resume from the first incomplete task
4. If crash repeats: escalate to user

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
