# Feasibility Validator Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect paths only — the subagent reads file content itself. For inline values (clarification block, requirements list), pass raw text.

| Placeholder | Source |
|-------------|--------|
| `{capabilities_path}` | `$PLAN_DIR/capabilities.md` — written by Step 5a |
| `{decisions_path}` | `$PLAN_DIR/decisions.md` — written by Step 5b |
| `{phase_grouping_path}` | `$PLAN_DIR/phase-grouping.md` — written by Step 5c.1 |
| `{task_drafts_path}` | `$PLAN_DIR/task-drafts.md` — written by Step 5c.2 (may have been edited by Step 5c.3 audit remediation) |
| `{audit_path}` | `$PLAN_DIR/audit.md` — written by Step 5c.3 |
| `{project_overview_path}` | `.workflow/project-overview.md` — pass the path, or `None` if the file doesn't exist |
| `{component_analysis_paths}` | Comma-separated paths of `.analysis.md` files referenced during Step 4b reads (or `None` if no fresh analysis docs were used) |
| `{requirements_in_scope}` | Bulleted list (inline) of confirmed in-scope requirements from Phase A. Format: one `- requirement text` per line. |
| `{user_clarification}` | Bulleted list (inline) of clarification answers and constraints from Phase A. Capture every nuance that affects feasibility evaluation. Format: one `- constraint or answer` per line. If no clarifications occurred, pass `- None — requirements were unambiguous as written`. |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected values. Keep purpose descriptions and rules. Pass everything below this line as the subagent prompt.

**Plan Artifacts:** capabilities at {capabilities_path}; decisions at {decisions_path}; phase grouping at {phase_grouping_path}; task drafts at {task_drafts_path}; audit at {audit_path}.

**Step 1 — Load all context in parallel.** Issue these Read calls in a single response:

- `{capabilities_path}` — Step 5a output (numbered capability list)
- `{decisions_path}` — Step 5b output (per-capability analysis blocks)
- `{phase_grouping_path}` — Step 5c.1 output (bulleted phase list with execution groups)
- `{task_drafts_path}` — Step 5c.2 output (per-phase task tables; may include audit-driven remediations)
- `{audit_path}` — Step 5c.3 output (Phase Composition Audit table with Status/Notes for every concern)
- `{project_overview_path}` — architectural context (skip if `None`)
- `{component_analysis_paths}` — analysis docs that informed the plan (skip if `None`)

**Step 2 — Read the in-scope requirements and user-clarification block below carefully.**

**In-scope requirements (from Phase A):**
{requirements_in_scope}

**User-clarification block (authoritative — do NOT flag gaps the user has already resolved):**
{user_clarification}

**Validator scope — what to check, what NOT to check.**

Your job is **capability coverage**, not implementation correctness. Apply this filter before flagging anything:

| Check | In scope? |
|-------|-----------|
| Does each `scope.in_scope` requirement map to at least one task whose `Done when` delivers it? | **YES** — this IS feasibility |
| Are cross-phase contracts properly sequenced (producer before consumer in execution groups)? | **YES** — planning-level invariant |
| Is the file path for each task plausible (exists, or sensible new location matching project layout)? | **YES** — at the directory / convention level only |
| Does the plan have a capability gap (e.g., a user-visible scenario that no task addresses)? | **YES** — flag as NOT_SATISFIED |
| Is the body schema of an API request correct across phases? | **NO** — execute-time. The executor reads existing API patterns and writes the right shape. |
| Is the exact symbol / file / component name correct? | **NO** — execute-time. The executor will Glob/Read to confirm names from source. |
| Does the transform output shape match the consumer's expected prop shape? | **NO** — execute-time. The executor reads the consumer's prop type and aligns. |
| Does the code use `useState` vs `useRef` vs Promise? Or `loadable()` vs `React.lazy()`? | **NO** — execute-time choice of mechanism. The plan describes the OUTCOME (e.g., "loading state stays up during chained save"); the mechanism is execute-time. |
| Are RTK Query / framework config flags correct (`keepUnusedDataFor`, invalidation tag lists, etc.)? | **NO** — execute-time. Executor matches existing endpoint conventions. |
| Is a UI element's exact JSX structure / prop spread / lazy-loading mechanism correct? | **NO** — execute-time. |

**Stop rule.** If you find yourself reading source code to verify a TypeScript shape, an exact property name, a transform's correctness, or a framework config flag — STOP. That's the executor's job, and the executor will catch it naturally when reading source at implementation time. Your job is verifying that the plan has all the tasks needed to deliver each capability, and that those tasks are properly sequenced.

**Why this scope.** A plan whose tasks describe HOW (URL paths, body schemas, exact names, transform code) invites validators to verify implementation correctness — and gets stuck doing the executor's job. A plan whose tasks describe WHAT (observable outcomes, the existence of capabilities) has less to be wrong about at plan time. The right feasibility question is "does the plan have all the steps needed to deliver the requirement?" — like checking that a recipe has "prep ingredients", "cook", "serve" sections — not "does the salt go in at minute 3 or minute 5?".

If a task description includes implementation detail that LOOKS wrong (e.g., a URL that doesn't match an existing pattern), DO NOT flag the detail as a feasibility defect. Instead, flag the OVER-SPECIFICATION itself: the task description is prescribing HOW when it should describe WHAT. Note it in Escalations with type `implementation_in_plan` so the planner can rewrite the task to be outcome-focused.

**Step 3 — Run the Requirement Satisfaction Trace.**

For each in-scope requirement, trace through the plan to find the tasks that, in combination, deliver it. The trace stays at the level of "which tasks contribute" — do NOT verify whether the tasks' implementation details are correct.

Produce one row per requirement:

- **Plan Path** — comma-separated list of tasks involved (e.g., `Phase 1 / task-02 (Add CSV serializer) → Phase 2 / task-01 (Wire serializer into endpoint)`)
- **Artifact After Plan Completes** — the user-visible / system-visible outcome that exists once all listed tasks complete. State the capability, not the implementation. GOOD: "An export endpoint that streams orders as CSV filtered by date range." BAD: "GET /api/reports/export returning streamed CSV with body `{from, to}` and `transformResponse` mapping `{...}` to `{...}`" — that's implementation detail; the executor decides it.
- **Verdict** — one of `DEMONSTRABLY_SATISFIED` (the listed tasks deliver the capability when read as outcomes — no gap requires reading source to disprove) / `PARTIALLY_SATISFIED` (a capability sub-step is missing — name which one) / `NOT_SATISFIED` (no task delivers this requirement at all)
- **Gap** — required for non-DEMONSTRABLY_SATISFIED verdicts. State the MISSING CAPABILITY, not the missing detail. GOOD: "No task wires the serializer's output into the HTTP response — Phase 1 produces the serializer but no Phase 2 task makes it reachable from the endpoint." BAD: "Task-02's body schema is missing the `status` field" — that's implementation detail, not a capability gap.

**Step 4 — Run the Premortem.**

Imagine 6 months have passed. The plan executed end-to-end. The feature shipped broken. Produce exactly 3 rows naming the most likely failure modes — but **only failure modes that are planning-level, not execute-time**. A planning-level failure is one a careful executor would NOT catch by reading source.

Planning-level failures (in scope):
- A user-visible scenario the plan doesn't cover (empty state, error path, large input, concurrent access — that no task addresses)
- A cross-phase coordination gap (Phase A's output and Phase B's input don't connect at all — not "the field name is wrong" but "no task wires them together")
- A capability the requirements demand but no task delivers
- A scaling / performance constraint surfaced in component intelligence but not addressed by any task

Execute-time failures (NOT in scope — exclude these):
- Wrong field name / typo in a symbol — the executor reads source
- Body schema mismatch between phases — the executor reads the consumer site
- Wrong transform logic — execute-time decision
- Race conditions inside one component's state machine — execute-time implementation choice (UNLESS the plan explicitly mis-specifies the coordination requirement)

Produce exactly 3 rows:

- **Failure Mode** — specific bad outcome AT THE CAPABILITY LEVEL (e.g., "Export endpoint times out for large date ranges because no task adds pagination", NOT "task-02's body schema is missing `pageSize`")
- **Plan Element Creating the Risk** — cite a specific element: task NAME, phase #, contract id, audit row, or a component-intelligence finding the plan doesn't address
- **Suggested Mitigation** — either a concrete plan revision (`Add pagination task to Phase 2`) OR an `ACCEPTED RISK: [concrete rationale]` annotation for user-weighing. The mitigation should be a NEW or MODIFIED task, not a re-spec of an existing task's implementation detail.

**Step 5 — Severity determination.**

Set Status.Result to:
- `PASS` — every Verdict is DEMONSTRABLY_SATISFIED AND every premortem Mitigation is either already covered by the plan as-written OR a clearly-justified ACCEPTED RISK
- `FAIL_REVISION_NEEDED` — at least one Verdict is PARTIALLY_SATISFIED or NOT_SATISFIED, OR at least one premortem Mitigation requires a plan revision
- `FAIL_AMBIGUOUS` — at least one row escalates to clarification (see Escalations rules below)

When uncertain between PASS and FAIL_REVISION_NEEDED, choose FAIL_REVISION_NEEDED — surfacing a false positive is cheap; missing a real feasibility gap is expensive.

**Rules for all rows:**
- Every claim cites a specific plan element (task name, phase #, contract id, file path, audit row, or component-intelligence finding). No vague claims.
- The user-clarification block is authoritative. Do NOT flag gaps the user has already resolved.
- Premortem mitigations must be minimal — scope them to the smallest plan change that addresses the risk. If the minimum change is structural (new phase, restructured plan), surface as an Escalation instead.
- Mitigations annotated `ACCEPTED RISK: [reason]` are only valid when the rationale references the user-clarification block, a project-overview principle, or a documented trade-off — never as a way to dismiss a real risk.

**Step 6 — Output in this exact format:**

```
## Status
**Result:** PASS | FAIL_REVISION_NEEDED | FAIL_AMBIGUOUS
**Trace_Pass_Count:** {N}/{Total}
**Critical_Gaps:** {count of NOT_SATISFIED entries}

## Requirement Satisfaction Trace
| Requirement | Plan Path | Artifact After Plan Completes | Verdict | Gap |
|-------------|-----------|------------------------------|---------|-----|
| {requirement text} | {plan elements} | {concrete artifact} | DEMONSTRABLY_SATISFIED ∣ PARTIALLY_SATISFIED ∣ NOT_SATISFIED | {gap or —} |

## Premortem
*Top 3 likely failure modes:*

| # | Failure Mode | Plan Element Creating the Risk | Suggested Mitigation |
|---|--------------|--------------------------------|----------------------|
| 1 | {specific failure} | {cited plan element} | {plan change OR "ACCEPTED RISK: [rationale]"} |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |

## Escalations
| Type | Description |
|------|-------------|
| {clarification_conflict ∣ ambiguous_requirement ∣ external_unknown ∣ implementation_in_plan} | {details with citation} |
```

Format rules:
- **Status.Result:** exact enum string from the three options
- **Trace_Pass_Count:** integer N (DEMONSTRABLY_SATISFIED count) over integer Total (total requirements)
- **Critical_Gaps:** integer count of NOT_SATISFIED verdicts
- **Requirement Satisfaction Trace:** one row per in-scope requirement, no exceptions
- **Premortem:** exactly 3 rows. If fewer than 3 genuine risks exist, the third row is `| 3 | None identified beyond top 2 — plan is well-anchored given the user-clarification block | — | — |` (this is rare; default to surfacing risks)
- **Escalations:** write `| None | None |` row if no escalations apply; never omit the section

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: PASS ∣ FAIL_REVISION_NEEDED ∣ FAIL_AMBIGUOUS | Decide: accept findings, apply revisions, or escalate to user |
| | `**Trace_Pass_Count**`: N/Total | Quick coverage gauge |
| | `**Critical_Gaps**`: integer count | Triage priority — high counts need plan revision |
| `## Requirement Satisfaction Trace` | Per row: `Requirement`, `Plan Path`, `Artifact After Plan Completes`, `Verdict`, `Gap` | For each Verdict ≠ DEMONSTRABLY_SATISFIED: locate the Gap and apply plan revision (update task drafts in 5c.2, re-run audit row in 5c.3) |
| `## Premortem` | Per row: `Failure Mode`, `Plan Element Creating the Risk`, `Suggested Mitigation` | For each Mitigation starting with `ACCEPTED RISK`: hold for Step 6 user-weighing. For plan-changing Mitigations: Edit the relevant artifact file (`task-drafts.md`, `decisions.md`, etc.), then re-spawn subagent. |
| `## Escalations` | Table: Type, Description | If any rows: present to user before continuing. Type enum: `clarification_conflict` (user clarification contradicts plan), `ambiguous_requirement` (in_scope item can't be evaluated), `external_unknown` (depends on unknown external system), `implementation_in_plan` (a task description prescribes HOW instead of WHAT — over-specification that should be rewritten as an outcome before proceeding) |

**Orchestrator action by Status.Result:**

- `PASS` → store trace + premortem for Step 6 presentation; proceed to Step 6
- `FAIL_REVISION_NEEDED` → Edit the affected artifact files in `$PLAN_DIR` (typically `task-drafts.md`, sometimes `decisions.md` or `phase-grouping.md`, and update `audit.md` to reflect new remediations); re-spawn subagent (max 2 revision rounds; if still failing after 2 rounds, escalate to user)
- `FAIL_AMBIGUOUS` → present escalations to user; pause for clarification; on receiving clarification, update the user-clarification block and re-spawn subagent
