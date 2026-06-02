---
description: |
  Execute an approved markdown plan-fast plan (`plan.md`) phase-by-phase, fast.
  Reads the plan, creates a plain-markdown `progress.md` tracker, spawns one lean
  executor per phase that implements tasks against their `Done when` outcomes,
  runs a code review per phase, and a single regression test run at the end.
  Tracks task status and realized cross-phase interfaces in `progress.md` — no
  JSON, no state CLI, no analysis gate, no mandatory TDD, no doc reconciliation.

  Triggers: "/execute-fast", "run the fast plan", "execute the markdown plan",
  "implement the plan-fast plan", "resume the fast execution".

  Use when the plan was produced by the fast planning skill (a `plan.md` with
  Provides/Needs task columns). Do NOT use for JSON plans with phase-{N}.json /
  state.json (use the full execution skill) — this skill has no CLI state layer.
---

# /execute-fast — Execute a Markdown Plan, Fast

You are executing an approved `plan.md` produced by the fast planning skill. Track progress and realized interfaces in a plain-markdown `progress.md`; implement each phase with one lean executor subagent; review each phase; run one regression test at the end. No JSON, no state CLI.

**Input:** `/execute-fast` (latest approved `plan.md`), `/execute-fast {plan-dir | plan.md path}`, or `/execute-fast --resume`
**Output:** Implemented code; `$PLAN_DIR/progress.md` tracking status + realized interfaces; per-phase reviews.

## Expert Vocabulary Payload

**Orchestration:** plan directory ($PLAN_DIR), group-sequential execution (A→B→C), per-phase executor spawn, one-shot reviewer spawn, markdown progress tracker (no CLI)
**Interface flow:** `Provides`/`Needs` task columns (planner-semantic), realized interface (executor-written), producer-writes / consumer-reads via `progress.md` `## Realized Interfaces`
**Quality:** Done-when verification (outcome observed, not just code written), per-phase code review (PASS/FAIL, max 2 fix rounds), single end-of-run regression test, non-negotiable security gates, documented TDD deviation
**Tracking:** task lifecycle (pending→active→done/failed/skipped) via row Edit, resume by re-reading progress.md, immutable plan.md

## Anti-Pattern Watchlist

### Plan Mutation
- **Detection:** Writing or editing `plan.md` during execution.
- **Resolution:** `plan.md` is immutable here. All execution state and realized detail go to `progress.md`. The planner owns `plan.md`; you only read it.

### JSON / CLI Assumption
- **Detection:** Reaching for `workflow_cli.py`, `state ...`, `plan.json`, `phase-{N}.json`, or `analysis check`.
- **Resolution:** This skill has none of that by design. Tracking is plain-markdown Edits to `progress.md`. There is no analysis gate and no `/doc-update` reconciliation — those were deliberately dropped for speed.

### Unverified Phase Completion
- **Detection:** Marking a phase complete because the executor returned, without confirming each task's `Done when` was actually verified in the executor output.
- **Resolution:** The executor must report HOW each `Done when` was verified. If a task row lacks verification evidence, treat the phase as PARTIAL and resolve before proceeding.

### Interface Loss
- **Detection:** Spawning a consumer phase without assembling the `received_interfaces` block from `progress.md` `## Realized Interfaces`; or a producer phase returns provided contracts but they were not written to `progress.md`.
- **Resolution:** Before each phase, assemble `received_interfaces` for every `Needs` cell. After each phase, confirm every `Provides` contract has a realized block in `progress.md`. Missing producer record → escalate, do not let the consumer guess.

### Infinite Fix Loop
- **Detection:** More than 2 reviewer fix rounds on the same phase.
- **Resolution:** After 2 failed rounds, STOP. Present findings to the user. Ask: fix manually, provide guidance, or skip review. Do not iterate further.

### Scope Creep
- **Detection:** Executor or orchestrator modifies files not in the task's `Files`.
- **Resolution:** Stay within declared scope. Out-of-scope necessities are reported in the executor envelope, not silently applied.

## Step 1: Resolve Plan & Load

Resolve `$PLAN_DIR`:

| Argument | Action |
|----------|--------|
| `--resume` | Find `.workflow/plans/*/` directories containing a `progress.md` whose header `Status` is not `completed`. One → use it. Multiple → list (name + first non-done task) and ask which. |
| Path to `plan.md` | Use its parent directory as `$PLAN_DIR` |
| Path to a directory | Use as-is |
| No argument | Find `.workflow/plans/*/plan.md` with `**Status:** approved`; if multiple, list and ask which |

Read `$PLAN_DIR/plan.md` in full — the `§capabilities`, `§analysis` (decisions/approaches), `§component-notes`, `§phases`, and `§tasks` (including `Provides`/`Needs`/`Done when`). Read `.workflow/project-overview.md` if it exists.

Confirm to the user: "Executing plan: `$PLAN_DIR/plan.md` — {N} phases, {T} tasks."

## Step 2: Create or Load progress.md

**Not resuming** — create `$PLAN_DIR/progress.md`:

```markdown
# Execution Progress: {Plan Name}

**Plan:** plan.md
**Started:** {YYYY-MM-DD}
**Start commit:** {git rev-parse HEAD}
**Status:** executing

## Task Tracker
| Phase | Group | Task ID | Name | Status | Verified by | Notes |
|-------|-------|---------|------|--------|-------------|-------|
| 1 | A | task-01 | [name] | pending | — | — |
| ... |

## Realized Interfaces
*(producer phases append one block per Provides contract; consumers read here)*

## Session Log
- {timestamp} — execution started
```

One Task Tracker row per task across all phases (read from `§tasks`). `Status` starts `pending`.

**Resuming** — read the existing `progress.md`. The resume point is the first task whose `Status` is not `done`/`skipped`; resume at that task's phase. Tell the user: "Resuming at Phase {N}, {task-id}."

## Step 3: Execute Phases in Group Order (A → B → C)

Process phases in execution-group order; within a group, process phases sequentially (simplicity over parallelism — this is the fast path, not the wide path). For each phase:

### Step 3a: Assemble received interfaces
For every `Needs Ph<X> contract-NN` in this phase's task rows: read the matching block under `## Realized Interfaces` in `progress.md` (the producer phase ran earlier and appended it). Concatenate them into the `received_interfaces` string.
- If a needed contract has **no realized block**: verify the producing phase is marked `done` in the Task Tracker. If it is done but the contract is missing → escalate to the user (producer didn't report it). If the producer hasn't run, that is a group-ordering defect in the plan — surface it and ask whether to reorder or abort. As a fallback only with user approval, pass the planned semantic from the plan's `Provides` cell and note the degradation.
- If this phase has no `Needs`: `received_interfaces` = `None`.

### Step 3b: Spawn the executor
Read the prompt template `.claude/skills/execute-fast/executor-fast-prompt.md`. Per its **For Orchestrator — Data to Collect**, collect the items (paths to `plan.md`, `progress.md`, project overview, `.claude/rules/security-gates.md`, `.claude/rules/quality-criteria.md`; the phase number; this phase's task rows verbatim; `received_interfaces`). Fill the `{placeholders}` in **For Subagent**. Spawn the **executor-fast** subagent (`.claude/agents/executor-fast.md`) **in foreground**, one spawn for the whole phase.

The executor updates `progress.md` itself (task rows → active/done/failed; appends realized-interface blocks for its `Provides` contracts).

### Step 3c: Parse the executor envelope
Per the template's **For Orchestrator — Expected Output**:
- `## Status` `**Result**`: `SUCCESS` → proceed. `PARTIAL`/`FAILURE` → read `## Escalations`, present blockers to the user, ask **retry** (re-spawn for the remaining tasks, max 2), **skip** (mark the failed task `skipped` in `progress.md` with reason), or **abort** (set progress `Status: paused`, stop).
- `## Tasks`: confirm every task has a verification-evidence note. Any task marked done without it → treat as PARTIAL and resolve.
- `## Public Interfaces`: confirm every `Provides` contract for this phase has a realized block in `progress.md` `## Realized Interfaces`. If the executor reported one but didn't write it, write it now from the envelope; if it's entirely missing and a later phase `Needs` it → escalate.

### Step 3d: Phase code review
Read `.claude/skills/execute-fast/reviewer-fast-prompt.md`. Per its **For Orchestrator — Data to Collect**, collect data (the phase's `git diff`; plan `§scope`, `§component-notes`, `§risks`, the phase goal line from `§phases`, this phase's task `Done when` cells; quality/security rule paths). Fill **For Subagent**. Spawn the **reviewer** subagent (`.claude/agents/reviewer.md`, reused) **in foreground**, one-shot.

Parse `## Status` `**Result**`: `PASS` → proceed. `FAIL` → read `**Failed Dimensions**` + each `**Fix Required**`; fix the issues yourself (you have full plan context), re-spawn the reviewer (max 2 fix rounds). Still failing after 2 → present to the user, ask how to proceed. Present the review outcome to the user before continuing.

### Step 3e: Phase close
Append to `progress.md` `## Session Log`: "{timestamp} — Phase {N} complete (review {PASS|user-approved})." Proceed to the next phase.

## Step 4: Final Regression Test (kept, conditional)

After ALL phases complete, detect a project test command **without any CLI/config**:
- Node: `package.json` → `scripts.test` (skip if it's the npm placeholder `"echo \"Error: no test specified\""`)
- Else: a `test`/`check` task in `Makefile`/`Taskfile`, or a runner named in `.workflow/project-overview.md` § Testing

If a real command is found: run it once via Bash (timeout 120000ms unless the overview states otherwise).
- Exit 0 → log "Regression test PASS" to `progress.md`.
- Exit non-zero → present output to the user; ask **fix** (fix, re-run, max 2 rounds), **skip**, or **abort**. Log the outcome.

If no runner is detectable: skip and log "Regression test skipped — no runner detected." Do **not** write speculative "if a runner is added later" text — state only what is true now.

(No `/doc-update`, no acceptance verifier, no analysis gate — deliberately out of this fast path. The knowledge layer is intentionally not reconciled; tell the user this if they expect doc updates.)

## Step 5: Completion

1. Edit the `progress.md` header: `**Status:** executing` → `completed`.
2. Append a final `## Session Log` line with the end commit (`git rev-parse HEAD`).
3. Present a summary: phases completed, tasks done/skipped/failed, review results, regression-test result, and the note that docs were not auto-reconciled.

## Resume Protocol

1. Resolve `$PLAN_DIR` (Step 1, `--resume` row).
2. Read `progress.md`; the resume point is the first non-`done`/`skipped` task → resume at its phase (re-run the whole phase if it was only partially done, since a phase is one executor spawn; tasks already `done` are reported to the executor as already-satisfied via their `Done when` and the realized interfaces in `progress.md`).
3. Tell the user the resume point, then continue Step 3 from that phase.

## Error Handling

- **Task failed:** mark the row `failed` + reason in `progress.md`; ask retry / skip / abort; never silently skip.
- **Executor crash mid-phase:** the executor's `progress.md` row Edits show which tasks finished; re-spawn for the remaining tasks only.
- **Needed interface missing:** Step 3a escalation — do not let a consumer guess a producer's realized signature.
- **Review loop (2 rounds failed):** stop, present to user, ask fix-manually / guidance / skip.

## Constraints
- Never write or edit `plan.md`. Never assume JSON/CLI/state.json.
- Security gates (`.claude/rules/security-gates.md`) are non-negotiable and override speed.
- TDD is a documented deviation on this path: verify by each task's `Done when` outcome, not by a mandatory test-first cycle. The end-of-run regression test is the only test gate.
- Do not invoke `/doc-update` or `/analyze` — they are out of scope for the fast path.

## Questions This Skill Answers

- "/execute-fast" / "/execute-fast --resume"
- "Run the markdown plan"
- "Implement the plan-fast plan"
- "Execute .workflow/plans/260518-foo/plan.md"
- "Resume the fast execution"
