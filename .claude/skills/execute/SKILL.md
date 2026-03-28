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
| `--resume` | Use the CLI to find the active plan → use the output path as `$PLAN_DIR` |
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

#### Step 2a: Phase Start

1. Use the CLI to mark the phase as in-progress
2. Use the CLI to read all tasks for the phase
3. Load relevant `.analysis.md` files (Level 1: frontmatter + CONTENT)
   - These should exist from planning. If missing → use the Skill tool to invoke `/analyze` as fallback

#### Step 2b: Phase Execution

Read the prompt template: `.claude/skills/execute/executor-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions
3. Spawn **one** executor subagent (`.claude/agents/executor.md`) for the entire phase, passing the filled **For Subagent** section as the prompt. The executor implements all tasks sequentially, tracking completion via CLI as it goes.

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

If **FAIL**: fix the issues yourself (you have full plan context from Step 1), then re-spawn the reviewer to verify (max 2 fix rounds). If still failing after 2 rounds, present findings to user and ask how to proceed.

Present review to user for approval before proceeding.

#### Step 2d: Playwright Check (conditional)

Only if the phase has `affected_components` that include UI components AND `.workflow/config.json` has `playwright_check: true`:
- Run Playwright to navigate affected pages
- Check: page loads, no console errors
- Report to user

#### Step 2e: Phase Completion

1. Use the CLI to mark the phase as completed
2. Run regression: tests from all prior completed phases still pass
3. Proceed to next group

**Note:** Documentation updates are NOT done per-phase. They happen once in the final reconciliation (Step 3) after all phases complete.

## Step 3: Final Reconciliation

After ALL phases complete. Three sub-steps, each a distinct concern.

### Step 3a: Reconciliation Pass (doc-update + overview + reflection — one pass)

This is a **single pass** over the execution results. Same data, processed together.

**1. Gather new data (don't re-read what's already in context):**

Already in your context from earlier steps:
- Plan summary (read at Step 1)
- Executor discoveries (from executor output reports — `## Discoveries` sections)

New data needed now:
- Use the CLI to get the execution start commit hash
- **Cumulative git diff:** `git diff {start_commit}..HEAD --name-only` — per-phase diffs don't capture cross-phase interactions
- **Affected components:** derive from the cumulative diff + phase files (deduplicate)

**2. For each affected component (one loop):**
- Use the Skill tool to invoke `/doc-update` with the component path, git diff, and plan context
- While processing: note if changes affect project-level architecture, modules, or data model

**3. After the component loop:**
- If any architecture/module/data model changes detected: update `.workflow/project-overview.md`
- Review all executor discoveries collected in step 1. For each **non-trivial** finding:
  - Present to user: "During execution, I discovered: {finding}. This should be documented in: {target document}. Proposed update: {content}"
  - If user agrees, apply the update:
    - Component behavior → update `.analysis.md` Hidden Details table
    - Wrong plan assumption (repeatable) → add rule to `.workflow/rules/planning/`
    - Code pattern correction → add/update rule in `.workflow/rules/code/`
    - Architecture/overview inaccuracy → update `.workflow/project-overview.md`
  - If user disagrees or trivial: skip

**Skip criteria for discoveries:** Don't surface findings that are:
- Already captured by the `/doc-update` invocations above (redundant)
- Trivial — typos, minor style differences, obvious things
- One-off with no future relevance
- Things the user told you during execution (they already know)

### Step 3b: Template Suggestion

Assess whether the completed work represents a **repeatable pattern**:
- Did this plan create something that will likely be built again with variations?
- Are there already similar components in the codebase that followed the same shape?

If yes, suggest: "This looks like a repeatable pattern ({reason}). Want to create a template now? The full execution context is still fresh."

If user agrees: use the Skill tool to invoke `/template-create` with `--from-session` flag.

Pass to the template-extractor agent:
1. **Plan summary** — what was built and why
2. **Component intelligence** — from plan + analysis docs
3. **Phase/task structure** — how work was decomposed
4. **Git diff** — `git diff {execution_start_commit}..HEAD`
5. **Execution discoveries** — collected in Step 3a
6. **Key decisions during execution** — what the executor adapted and why

If user declines: fine. They can run `/template-create` later.

### Step 3c: Final Verification

1. Run full test suite
2. Use the CLI to mark the entire execution as complete
3. Use the CLI to display the final execution progress
4. Present execution summary to user

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
