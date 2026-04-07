---
description: |
  Execute an approved plan phase-by-phase with TDD enforcement, code review,
  state tracking, knowledge persistence, and doc updates. Handles executor
  subagent orchestration, analysis gates, discovery/decision capture, and
  final reconciliation. Use when the user wants to run a plan, start
  implementation, resume interrupted work, or says "execute this" — even if
  they don't say "/execute." Also triggers for resuming paused executions
  and continuing from a specific phase.
  Do NOT use for planning (use /plan), analyzing components (use /analyze),
  or updating docs without a plan (use /doc-update with component path).
---

# /execute — Execute Plan

You are executing an approved plan phase-by-phase. Track state, enforce TDD, run reviews, maintain codebase knowledge.

**CLI reference:** `.claude/scripts/workflow_cli.reference.md` — use for all plan/phase/state operations. Read it to find exact command syntax.

**CRITICAL: Every CLI command MUST include `--plan-dir $PLAN_DIR`.** Without it, the CLI auto-resolves to the latest plan alphabetically, which silently targets the wrong plan when multiple plans exist.

**Input:** `/execute` (uses latest approved plan), `/execute {plan-path}`, or `/execute --resume`
**Output:** Implemented code, updated state, reviewed and documented

## Expert Vocabulary Payload

**Orchestration:** plan directory ($PLAN_DIR), group-sequential execution (A→B→C), phase-parallel execution, executor subagent (per-phase spawn), reviewer subagent (one-shot), prompt template filling ({placeholders})

**State Tracking:** execution start commit, phase lifecycle (pending→in_progress→completed), task lifecycle (pending→active→completed/failed/skipped), substep tracking (done/next), session log, resume point

**Analysis Gate:** component freshness check (fresh/stale/missing), recursive dependency check (--recursive), progressive loading level (0/1/2), analysis-first principle

**Knowledge Persistence:** discovery persistence (state add-discovery), decision persistence (state add-decision), CLI-based state storage, context-compression-safe, knowledge layer reconciliation (/doc-update)

**Quality Enforcement:** TDD policy (tests first), dimension-based code review (PASS/FAIL), fix round (max 2), regression detection, Playwright smoke check, test execution gate (independent test run, conditional on config), acceptance verification (spec-based independent check, test mode vs reason mode), cross-phase integration check

## Anti-Pattern Watchlist

### Silent $PLAN_DIR Omission
- **Detection:** CLI commands run without `--plan-dir $PLAN_DIR`. Output targets the wrong plan. State updates appear in an unexpected plan directory.
- **Resolution:** Every CLI call must include `--plan-dir $PLAN_DIR`. Resolve $PLAN_DIR in Step 1a and use it for ALL subsequent commands without exception.

### Per-Phase Doc Update
- **Detection:** Invoking `/doc-update` or `/analyze` after each phase completes, instead of waiting for final reconciliation.
- **Resolution:** Documentation updates happen ONCE in Step 3 after ALL phases complete. Per-phase updates waste tokens, create partial state, and risk inconsistency when later phases change the same components.

### Discovery Loss
- **Detection:** Executor reports discoveries or decisions in its output, but the orchestrator does not call `state add-discovery` / `state add-decision` to persist them. Knowledge exists only in conversation context where it's vulnerable to compression.
- **Resolution:** For EVERY row in executor `## Discoveries` and `## Decisions`, immediately call the corresponding CLI persistence command. Verify with `state get-discoveries` if uncertain.

### Infinite Fix Loop
- **Detection:** More than 2 reviewer fix rounds on the same phase. The orchestrator keeps fixing and re-spawning the reviewer without escalating.
- **Resolution:** After 2 failed fix rounds, STOP. Present review findings to user. Ask: fix manually, provide guidance, or skip review. Do NOT iterate further.

### Scope Creep
- **Detection:** Executor or orchestrator modifies files not listed in the plan's `tasks[].files` or `affected_components`. Changes spread beyond the plan's declared scope.
- **Resolution:** Only modify files within the plan's scope. If a necessary change is out of scope, report it in Discoveries — do not silently extend the plan.

### Skipped Analysis Gate
- **Detection:** Phase execution begins without running `analysis check --recursive` on affected components. Executor receives stale or missing component intelligence.
- **Resolution:** Step 2a is mandatory. For every component in `affected_components`, check freshness. Stale/missing → invoke `/analyze` before spawning the executor.

### TDD Bypass
- **Detection:** Implementation code written without tests, and the task does not fall under a documented TDD exception (UI layout, config, types, prototypes, generated code).
- **Resolution:** Default is tests first. If skipping, the reason must match a documented exception and be stated in the executor output. "It seemed obvious" is not an exception.

### Skipped Acceptance Verification
- **Detection:** Phase has non-empty `acceptance_specs` but Step 2c.1 is not executed. Or verification fails and orchestrator proceeds without user approval.
- **Resolution:** If `acceptance_specs` exist, Step 2c.1 is mandatory. Failures must be presented to the user — do not silently skip or auto-approve.

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
- **Persist discoveries:** For each row in `## Discoveries`, call `state add-discovery {phase_num} {component} "{what}" "{why}" "{risk}" "{test_suggestion}" {category} --plan-dir $PLAN_DIR`
- **Persist decisions:** For each row in `## Decisions`, call `state add-decision {phase_num} {component} "{decision}" "{reasoning}" "{alternatives}" --plan-dir $PLAN_DIR`
- Read `## Result` → `**Files Changed**` for the reviewer, `**Tests Written/Passing**` for verification

The executor handles task-level state tracking internally:
- Marks each task active before starting it
- Marks each task complete when done
- If it hits a blocker, it stops and reports — the orchestrator handles error recovery

**Why per-phase, not per-task:** Each subagent spawn costs ~4000 tokens of context. A 4-task phase costs 16,000 tokens with per-task spawning vs 4,000 tokens per-phase. The executor also builds naturally on its own work — no re-reading files it just created.

#### Step 2b.1: Test Execution Gate (conditional)

Only if `.workflow/config.json` exists AND has a non-null `test_command` field.

1. Read test command: use CLI `config get test_command`
2. Read timeout: use CLI `config get test_command_timeout` (default 120000 if null)
3. Run the test command via Bash with the specified timeout
4. Parse result:
   - **Exit 0** → tests pass. Log: `state log "Test gate PASS" --plan-dir $PLAN_DIR`. Proceed to Step 2c. Save test output for the reviewer (Step 2c).
   - **Exit non-zero** → tests fail.
     - Present test output to user
     - Ask: **fix** (fix failures yourself, re-run, max 2 fix rounds), **skip** (proceed to review anyway), or **abort**
     - Log: `state log "Test gate {PASS|FAIL|SKIPPED} — {summary}" --plan-dir $PLAN_DIR`

If `.workflow/config.json` is missing or has no `test_command`: skip this step entirely. Log: `state log "Test gate skipped — no test_command configured" --plan-dir $PLAN_DIR`

**Why this step exists:** The executor self-reports test counts but independent test execution catches false reports before expensive code review.

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

#### Step 2c.1: Acceptance Verification (conditional)

Only if the phase has non-empty `acceptance_specs` in `phase-{N}.json`.

1. **Determine mode:**
   - Read `.workflow/config.json` → `acceptance_mode` via CLI `config get acceptance_mode` (default: `"auto"`)
   - `auto`: use `test` when `test_command` exists, `reason` otherwise
   - `test` or `reason`: use that mode directly

2. Read the prompt template: `.claude/skills/execute/acceptance-verifier-prompt.md`
3. Collect each data item listed in **For Orchestrator** from its specified source
4. Fill `{placeholders}` in **For Subagent** with collected data
5. Spawn an **acceptance-verifier subagent** (`.claude/agents/acceptance-verifier.md`), passing the filled **For Subagent** section as the prompt — one-shot, fresh spawn

**Parse output** per `acceptance-verifier-prompt.md` § "For Orchestrator — Expected Output":
- Read `## Status` → `**Result**`: `PASS`, `FAIL`, or `PARTIAL`
- If `FAIL` or `PARTIAL`: read `**Failed Specs**` for the list, then extract each failed spec's `**Gap**` from `## Specs`

**If PASS:** Log and proceed to Step 2d. `state log "Acceptance verification PASS — {passed}/{total} specs" --plan-dir $PLAN_DIR`

**If FAIL or PARTIAL:**
- Present failed specs with evidence and gaps to user
- Ask: **fix** (fix the gaps yourself based on gap descriptions, then re-spawn verifier, max 2 fix rounds), **skip** (proceed anyway), or **abort**
- If fix: apply fixes, re-spawn acceptance verifier. After 2 failed rounds, present to user and ask how to proceed.
- Log: `state log "Acceptance verification {PASS|FAIL|SKIPPED} — {passed}/{total}" --plan-dir $PLAN_DIR`

If phase has no `acceptance_specs` or the array is empty: skip this step. Log: `state log "Acceptance verification skipped — no specs" --plan-dir $PLAN_DIR`

**Why this step exists:** The executor and code reviewer share correlated blind spots (both are LLM static analysis). Acceptance verification independently checks whether the implementation actually delivers the requirements using structured specifications authored during planning.

#### Step 2d: Playwright Check (conditional)

Only if the phase has `affected_components` that include UI components AND `.workflow/config.json` has `playwright_check: true`:
- Run Playwright to navigate affected pages
- Check: page loads, no console errors
- Report to user

#### Step 2e: Phase Completion

1. Use the CLI to mark the phase as completed
2. Proceed to next group

**Note:** Documentation updates are NOT done per-phase. They happen once in the final reconciliation (Step 3) after all phases complete.

## Step 2.5: Cross-Phase Integration Check (conditional)

After ALL phases in ALL groups complete, before Step 3.

Only if (a) more than one phase was executed AND (b) `.workflow/config.json` has a non-null `test_command` (via CLI `config get test_command`):

1. Run the test command via Bash
2. **Exit 0** → integration check passes. Log: `state log "Integration check PASS" --plan-dir $PLAN_DIR`. Proceed to Step 3.
3. **Exit non-zero** → cross-phase regression detected.
   - Identify which tests fail from the output
   - Present to user: "Cross-phase integration check failed. These tests may have been broken by interactions between phases."
   - Ask: **fix** (fix regressions, re-run), **skip** (proceed to reconciliation), or **abort**
   - Log outcome: `state log "Integration check {PASS|FAIL|SKIPPED}" --plan-dir $PLAN_DIR`

If single phase or no `test_command`: skip. Log: `state log "Integration check skipped — {reason}" --plan-dir $PLAN_DIR`

**Why this step exists:** Per-phase tests run in isolation. Phase 3 may break Phase 1's tests through shared dependencies, config changes, or type modifications. This catches regressions that per-phase testing cannot.

## Step 3: Final Reconciliation

After ALL phases complete (and integration check passes or is skipped).

### Step 3a: Knowledge Layer Update

Use the Skill tool to invoke `/doc-update` (no arguments). Doc-update auto-detects the active plan via CLI and reads discoveries and decisions from state.json (persisted during Step 2b via CLI commands). Plan summary is read from plan.json.

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
- Do NOT read or edit state.json directly — always use the CLI
- Do NOT proceed past a FAILED review without fixing issues or getting user approval
- Do NOT skip the final reconciliation step (Step 3) — even if all phases passed review

## Questions This Skill Answers

- "Execute this plan"
- "Run the plan"
- "/execute"
- "Start implementation"
- "Resume the execution"
- "Continue from where we left off"
- "/execute --resume"
- "Implement the approved plan"
- "Start building this"
- "Run phase 2 of the plan"
- "Pick up where we stopped"
- "Execute .workflow/plans/260328-feature/plan.json"
