# Feasibility Validator Prompt Template (plan-fast — single plan.md)

This contract drives the `feasibility-validator` agent against a **single markdown plan** (`plan.md`), not the 5-file artifact set. The prompt below is self-sufficient — it tells the subagent to read one file and overrides any prior expectation of separate capability/decision/audit files.

## For Orchestrator — Data to Collect

Collect paths as raw strings; pass inline blocks as raw bulleted text. Do not paste file content the subagent can read itself.

| Placeholder | Source |
|-------------|--------|
| `{plan_md_path}` | `$PLAN_DIR/plan.md` — the in-progress plan (Scope, Capabilities, Per-Capability Analysis, Component Notes, Phases, Tasks, Composition Audit all present; Feasibility/Risks may be empty) |
| `{project_overview_path}` | `.workflow/project-overview.md` — pass the path, or `None` if the file doesn't exist |
| `{requirements_in_scope}` | Inline bulleted list of confirmed in-scope requirements from Phase A (Steps 2–3). One `- requirement` per line. |
| `{user_clarification}` | Inline bulleted list of every clarification answer/constraint from Phase A. One `- answer or constraint` per line. If none occurred, pass `- None — requirements were unambiguous as written`. |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected values. Pass everything below this line as the subagent prompt.

You are validating a single markdown execution plan. **Ignore any instinct to load five separate artifact files — this plan is one file.**

**Step 1 — Load context in parallel.** Issue these Read calls in a single response:
- `{plan_md_path}` — the whole plan. Its sections: `## Scope`, `## Capabilities`, `## Per-Capability Analysis & Approach Selection`, `## Component Notes`, `## Phases`, `## Tasks` (per-phase tables with a `Done when` column), `## Composition Audit` (table with Status/Notes).
- `{project_overview_path}` — architectural context (skip if `None`).

**Step 2 — Read the in-scope requirements and user-clarification block carefully.**

**In-scope requirements (from Phase A):**
{requirements_in_scope}

**User-clarification block (authoritative — do NOT flag gaps the user already resolved):**
{user_clarification}

**Validator scope — what to check, what NOT to check.** Your job is **capability coverage**, not implementation correctness.

| Check | In scope? |
|-------|-----------|
| Does each in-scope requirement map to ≥1 task whose `Done when` delivers it? | **YES** — this IS feasibility |
| Are cross-phase dependencies sequenced (producer phase's execution group strictly earlier than consumer's)? | **YES** — planning-level invariant |
| Is each task's file path plausible (exists, or a sensible new location for the project layout)? | **YES** — directory / convention level only |
| Is there a capability gap (a user-visible scenario no task addresses)? | **YES** — flag as NOT_SATISFIED |
| Is an API body schema / exact symbol / component name / transform shape correct? | **NO** — execute-time; the executor reads source |
| Mechanism choices (`useState` vs `useRef`, `loadable` vs `lazy`, framework config flags)? | **NO** — execute-time |

**Stop rule.** If you are reading source to verify a type shape, an exact name, a transform's correctness, or a config flag — STOP; that's the executor's job. Verify the plan has all the tasks needed to deliver each capability, properly sequenced. If a task's `Done when` prescribes HOW (URL, body schema, exact names), do NOT flag the detail as wrong — flag the over-specification itself via the `implementation_in_plan` escalation.

**Step 3 — Requirement Satisfaction Trace.** For each in-scope requirement, trace which tasks (by Phase / task-id / name) together deliver it, name the concrete user/system-visible artifact that exists once those tasks complete (state the capability, not the implementation), and assign a Verdict: `DEMONSTRABLY_SATISFIED` (tasks deliver the capability read as outcomes) / `PARTIALLY_SATISFIED` (a sub-step is missing — name it) / `NOT_SATISFIED` (no task delivers it). Non-satisfied verdicts require a Gap stating the missing **capability**, not a missing detail.

**Step 4 — Premortem.** Six months later the plan shipped broken. Produce exactly 3 planning-level failure modes (ones a careful executor would NOT catch by reading source): uncovered user-visible scenario, cross-phase coordination gap (no task wires producer to consumer), a demanded capability no task delivers, or a component-note constraint no task addresses. Exclude execute-time failures (wrong field name, schema mismatch, transform logic, intra-component race). Each row: the capability-level failure, the cited plan element creating the risk (task name / phase # / audit row / component note), and a minimal mitigation (a NEW or MODIFIED task) OR `ACCEPTED RISK: [rationale grounded in the clarification block or a project-overview principle]`.

**Step 5 — Severity.**
- `PASS` — every Verdict DEMONSTRABLY_SATISFIED AND every premortem mitigation already covered by the plan or a justified ACCEPTED RISK
- `FAIL_REVISION_NEEDED` — any PARTIALLY_SATISFIED / NOT_SATISFIED, OR any premortem mitigation requiring a plan revision
- `FAIL_AMBIGUOUS` — any row needs clarification (see Escalations)

When uncertain between PASS and FAIL_REVISION_NEEDED, choose FAIL_REVISION_NEEDED.

**Rules:** every claim cites a specific plan element; the clarification block is authoritative; mitigations are minimal (escalate if the minimum change is structural); ACCEPTED RISK is valid only when its rationale references the clarification block, a project-overview principle, or a documented trade-off.

**Step 6 — Output in this exact format:**

```
## Status
**Result:** PASS | FAIL_REVISION_NEEDED | FAIL_AMBIGUOUS
**Trace_Pass_Count:** {N}/{Total}
**Critical_Gaps:** {count of NOT_SATISFIED entries}

## Requirement Satisfaction Trace
| Requirement | Plan Path | Artifact After Plan Completes | Verdict | Gap |
|-------------|-----------|------------------------------|---------|-----|
| {requirement} | {Phase / task-id / name list} | {concrete artifact} | DEMONSTRABLY_SATISFIED ∣ PARTIALLY_SATISFIED ∣ NOT_SATISFIED | {gap or —} |

## Premortem
*Top 3 likely failure modes:*

| # | Failure Mode | Plan Element Creating the Risk | Suggested Mitigation |
|---|--------------|--------------------------------|----------------------|
| 1 | {specific capability-level failure} | {cited plan element} | {plan change OR "ACCEPTED RISK: [rationale]"} |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |

## Escalations
| Type | Description |
|------|-------------|
| {clarification_conflict ∣ ambiguous_requirement ∣ external_unknown ∣ implementation_in_plan} | {details with citation} |
```

Format rules:
- **Result:** exact enum string
- **Trace_Pass_Count:** integer N (DEMONSTRABLY_SATISFIED count) over integer Total (total in-scope requirements)
- **Critical_Gaps:** integer count of NOT_SATISFIED verdicts
- **Requirement Satisfaction Trace:** one row per in-scope requirement, no exceptions
- **Premortem:** exactly 3 rows. If fewer than 3 genuine risks, row 3 is `| 3 | None identified beyond top 2 — plan is well-anchored given the clarification block | — | — |`
- **Escalations:** write `| None | None |` if none apply; never omit the section

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: PASS ∣ FAIL_REVISION_NEEDED ∣ FAIL_AMBIGUOUS | Decide: accept, revise, or escalate |
| | `**Trace_Pass_Count**`: N/Total | Coverage gauge |
| | `**Critical_Gaps**`: integer | Triage priority |
| `## Requirement Satisfaction Trace` | `Requirement`, `Plan Path`, `Artifact After Plan Completes`, `Verdict`, `Gap` | For each Verdict ≠ DEMONSTRABLY_SATISFIED: Edit the Tasks/Phases sections of `plan.md` to close the Gap |
| `## Premortem` | `Failure Mode`, `Plan Element Creating the Risk`, `Suggested Mitigation` | `ACCEPTED RISK` → hold for the Step 10 user checkpoint + add to Risks. Plan-changing mitigation → Edit `plan.md`, then re-spawn. |
| `## Escalations` | Type, Description | If any rows: present to user before continuing |

**Orchestrator action by Result:**
- `PASS` → paste the Trace + Premortem verbatim into the `## Feasibility` section of `plan.md`; fold mitigations/ACCEPTED RISKs into `## Risks`; proceed to Step 10
- `FAIL_REVISION_NEEDED` → Edit the affected sections of `plan.md` (Tasks, Phases, or Per-Capability Analysis); re-spawn (max 2 revision rounds; if still failing after 2, present findings to the user and ask how to proceed)
- `FAIL_AMBIGUOUS` → present Escalations to the user; on receiving clarification, update the inline `{user_clarification}` block and re-spawn

Escalation type meanings: `clarification_conflict` (clarification block contradicts the plan), `ambiguous_requirement` (an in-scope item can't be evaluated), `external_unknown` (depends on an unverified external system), `implementation_in_plan` (a `Done when` prescribes HOW — rewrite it as an outcome before proceeding).
