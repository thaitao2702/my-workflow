# Executor-Fast Prompt Template

Drives the `executor-fast` agent for one phase of a markdown `plan.md`. Tracking is plain-markdown `progress.md` — no JSON, no CLI.

## For Orchestrator — Data to Collect

Collect paths as raw strings; pass computed extracts inline. The subagent reads file content itself.

| Placeholder | Source |
|-------------|--------|
| `{plan_md_path}` | `$PLAN_DIR/plan.md` |
| `{progress_md_path}` | `$PLAN_DIR/progress.md` |
| `{project_overview_path}` | `.workflow/project-overview.md`, or `None` if absent |
| `{rules_paths}` | **Every** `.md` file under `.workflow/rules/` — glob `.workflow/rules/**/*.md` (recursive; all subfolders), pass all of them, no hard-coded subset. Comma-separated raw paths. `None` if the folder has no `.md` files. |
| `{phase_num}` | The phase number being executed |
| `{phase_goal}` | The phase's line from plan.md `§phases` (name + intent), inline |
| `{phase_tasks}` | This phase's task rows from `§tasks` verbatim (markdown table: Task ID, Name, Capability, Files, Provides, Needs, Done when), inline |
| `{received_interfaces}` | Assembled realized-interface blocks for every `Needs` contract this phase consumes (from `progress.md` `## Realized Interfaces`), inline. `None` if this phase has no `Needs`. |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected values. Pass everything below this line as the subagent prompt.

You are implementing **Phase {phase_num}** of a markdown execution plan. Tracking is plain-markdown — there is no JSON, no `workflow_cli.py`, no `state.json`. Never write to `plan.md`; it is immutable. All status and realized-interface updates go to `progress.md`.

**Phase goal:** {phase_goal}

**Your tasks (in order):**
{phase_tasks}

**Realized interfaces you may consume (`Needs`):**
{received_interfaces}

**Step 1 — Load context in parallel.** Issue these Read calls in one response: `{plan_md_path}` (for `§component-notes` conventions, `§analysis` committed approaches, and your task cells), `{progress_md_path}` (your Task Tracker rows + existing `## Realized Interfaces`), `{project_overview_path}` (skip if `None`), and **every path in `{rules_paths}`** (read them all — they are the rules you must obey; skip if `None`).

**Step 2 — For each task, in table order:**
1. Edit its row in `{progress_md_path}` Task Tracker: `Status` → `active`.
2. If the task `Needs Ph<X> contract-NN`: use the realized signature from the realized-interfaces block above (or `## Realized Interfaces` in progress.md). Do not re-derive it from the producer's source unless that record is missing — if missing, stop and escalate (do not guess).
3. Implement so the task's **`Done when`** outcome becomes true. Touch only files in the task's `Files` list. Follow patterns from `§component-notes` and the project overview. Apply **every rule file in `{rules_paths}`** at all times — these override speed and are non-negotiable.
4. **Verify the outcome.** Run the build/command, read the produced artifact, or exercise the code path — concrete evidence that `Done when` holds. "Code written" ≠ "done".
5. If the task `Provides contract-NN`: append a block under `## Realized Interfaces` in `{progress_md_path}`:
   ```
   ### Ph{phase_num} contract-NN — <name>
   - **signature:** <the realized signature/shape consumers call>
   - **usage_example:** <one minimal example>
   - **error_shape:** <what failure looks like to a consumer>
   - **file:** <path where it lives>
   ```
6. Edit the task row: `Status` → `done`, fill `Verified by` with the evidence from step 4. If you could not complete it: `Status` → `failed`, `Notes` → one-line reason; continue to the next task only if it does not depend on this one, else stop.
7. Emit the drift checkpoint, then proceed:
   ```
   ---CHECKPOINT---
   Done: [task id + outcome now true]
   Next: [next task id + its Done-when]
   Goal: [phase goal, one line]
   ---END CHECKPOINT---
   ```

**Step 3 — TDD note.** This fast path does not require tests-first. Verify by the `Done when` outcome (step 2.4). You MAY add a test only if the project already has a runner and a test is the clearest outcome proof — never build a test harness the plan didn't ask for.

**Step 4 — Output in this exact format:**

```
## Status
**Result:** SUCCESS | PARTIAL | FAILURE
**Tasks_Done:** {N}/{Total}

## Tasks
| Task ID | Status | Done-when verified by |
|---------|--------|-----------------------|
| task-01 | done ∣ failed ∣ skipped | {concrete evidence, or failure reason} |

## Public Interfaces
| Contract | signature | usage_example | error_shape | file |
|----------|-----------|---------------|-------------|------|
| Ph{phase_num} contract-NN | ... | ... | ... | ... |
*(write `| None | — | — | — | — |` if this phase Provides no contracts)*

## Escalations
| Type | Description |
|------|-------------|
| {missing_interface ∣ unverifiable_done_when ∣ out_of_scope_change ∣ security_gate ∣ blocked} | {detail with task id} |
*(write `| None | None |` if no escalations)*
```

Format rules:
- `## Status` first, `## Escalations` last; exact enum strings.
- `Result`: `SUCCESS` = all tasks done + verified; `PARTIAL` = some done, some failed/blocked; `FAILURE` = no progress.
- Every `done` task MUST have non-empty `Done-when verified by` evidence.
- `## Public Interfaces` mirrors what you appended to `progress.md` — the orchestrator cross-checks.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: SUCCESS ∣ PARTIAL ∣ FAILURE; `**Tasks_Done**`: N/Total | Proceed vs recover |
| `## Tasks` | Per row: `Status`, `Done-when verified by` | Any `done` lacking verification → treat phase as PARTIAL and resolve before review |
| `## Public Interfaces` | Per contract: signature, usage_example, error_shape, file | Confirm each appears under `## Realized Interfaces` in `progress.md`; if reported but unwritten, write it; if missing and a later phase Needs it → escalate to user |
| `## Escalations` | Type, Description | Handle before proceeding. `missing_interface` → producer-order/record problem; `security_gate` → do not override; `out_of_scope_change` → decide scope; `unverifiable_done_when` → user decision; `blocked` → retry/skip/abort |

**Orchestrator action by Result:**
- `SUCCESS` → Step 3d (phase code review)
- `PARTIAL` → present escalations + failed tasks to user; retry remaining (re-spawn, max 2), skip (mark row `skipped` + reason), or abort (progress `Status: paused`)
- `FAILURE` → present to user; do not proceed to review until resolved
