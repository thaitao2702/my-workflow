# Reviewer-Fast Prompt Template

Drives the **existing** `reviewer` agent (`.claude/agents/reviewer.md`) against one phase of a markdown `plan.md`. Sourced from markdown (no `plan.json`/`phase-{N}.json`); the "test coverage" dimension is replaced by "Done-when verification" because this fast path has no per-task tests.

## For Orchestrator — Data to Collect

Collect paths as raw strings; pass computed extracts inline.

| Placeholder | Source |
|-------------|--------|
| `{code_changes}` | `git diff` for this phase's commits/working tree, inline |
| `{scope}` | plan.md `§scope` (in/out), inline |
| `{committed_approaches}` | plan.md `§analysis` — the `Committed approach` lines for the capabilities this phase covers, inline |
| `{component_notes}` | plan.md `§component-notes` (constraints/patterns), inline |
| `{risks}` | plan.md `§risks`, inline |
| `{phase_goal}` | The phase's line from plan.md `§phases`, inline |
| `{phase_task_outcomes}` | This phase's task rows from `§tasks` — Task ID, Files, `Provides`, `Done when` — inline |
| `{rules_paths}` | **Every** `.md` file under `.workflow/rules/` — glob `.workflow/rules/**/*.md` (recursive; all subfolders), pass all of them, no hard-coded subset. Comma-separated raw paths (`None` if the folder has no `.md` files). This is the **same rule set the executor obeys**. |
| `{realized_interfaces}` | The `## Realized Interfaces` blocks this phase produced or consumed, from `progress.md`, inline (or `None`) |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep the dimensions. Pass everything below this line as the subagent prompt.

You are reviewing the code changes of one phase of a markdown execution plan. There is no per-task test suite on this path — correctness is judged by whether each task's **`Done when`** outcome is realized in the diff. Review statically; do not run tests.

**Code Changes (the diff under review — every finding cites lines from this):**
{code_changes}

**Scope (flag anything outside these boundaries):**
{scope}

**Committed Approaches (implementation must align with these planner decisions):**
{committed_approaches}

**Component Notes (constraints the code must respect):**
{component_notes}

**Risks & Mitigations (flag any ignored or mishandled):**
{risks}

**Phase Goal:**
{phase_goal}

**Task Outcomes to verify (`Done when` per task — mandatory, not aspirational):**
{phase_task_outcomes}

**Realized Interfaces (provided/consumed cross-phase contracts):**
{realized_interfaces}

**Context files (load in parallel before reviewing) — every rule you review against:** {rules_paths}

**Review against all 6 dimensions:**

1. **Done-when verification** — for every task, the diff demonstrably realizes its `Done when` outcome. FAIL if code is present but the stated observable outcome is not actually achieved, or a task's outcome has no corresponding change.
2. **Scope compliance** — only files within the phase's task `Files` changed; no work outside `§scope`.
3. **Architectural alignment** — implementation matches the `Committed approach` lines and respects `§component-notes` constraints.
4. **Risk mitigation** — risks in `§risks` relevant to this phase are handled, not ignored or mis-mitigated.
5. **Code quality & security** — passes every loaded rule in {rules_paths}; no security-gate violation (hardcoded secrets, injection, missing auth, destructive ops).
6. **Convention & interface compliance** — matches existing codebase patterns; any `Provides` contract's realized interface is internally consistent with how consuming code (if in this diff) uses it.

**Output in this exact format:**

```
## Status
**Result:** PASS | FAIL
**Passed:** {N}/6
**Failed Dimensions:** [{dimension names, or none}]

## Dimensions
### {N}. {Dimension Name}
**Result:** PASS | FAIL
**Evidence:** {specific file:line reference from the diff}
**Fix Required:** {what needs fixing} | —

## Escalations
| Type | Dimension | Description |
|------|-----------|-------------|
| {ambiguous_criteria ∣ conflicting_rules ∣ unclassifiable} | {dimension} | {detail} |
*(write `| None | None | None |` if no criteria issues)*
```

- `PASS` only if all 6 dimensions pass. Every PASS must cite what was checked — no rubber-stamp.
- Every dimension appears with an explicit PASS/FAIL. Use `—` for Fix Required only on PASS.
- Findings only — no preamble or summaries between findings.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: PASS ∣ FAIL; `**Passed**`: N/6; `**Failed Dimensions**` | Proceed vs fix |
| `## Dimensions` | Per dimension: `**Result**`, `**Evidence**`, `**Fix Required**` | The concrete fixes to apply if FAIL |
| `## Escalations` | Type, Dimension, Description | Criteria issues to resolve before re-review. Type enum: `ambiguous_criteria`, `conflicting_rules`, `unclassifiable` |

**Orchestrator action by Result:**
- `PASS` → present the review to the user, then close the phase (Step 3e)
- `FAIL` → apply each `Fix Required` yourself (you hold full plan context), re-spawn this reviewer (max 2 fix rounds). Still failing after 2 → present findings to the user; ask fix-manually / guidance / skip-review.
