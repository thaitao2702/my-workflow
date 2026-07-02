# Feasibility Validator Prompt Template (plan-fast — single plan.md)

Drives the `feasibility-validator` agent against a **single markdown plan** (`plan.md`). The prompt below overrides the agent's default methodology in two ways: it tells the subagent to read **one** file (not the five-file artifact set the persona describes) and it requires a **two-phase load** so that scenario questions are pre-registered from the requirement *before* the plan is read.

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

You are validating a single markdown execution plan. **Ignore any instinct to load five separate artifact files — this plan is one file.** This task also requires a **strict two-phase load**: you must generate scenario questions from the requirement BEFORE reading the plan. Reading the plan first would let your questions get shaped by what the plan happens to contain, defeating the purpose of an independent review.

### Phase 1 — Load REQUIREMENT context only

Issue these Read calls (and ONLY these) in a single response:
- `{project_overview_path}` — architectural context (skip if `None`).

Then read the inline blocks below carefully. **Do NOT Read `{plan_md_path}` in this phase.** Pre-registration depends on this ordering.

**In-scope requirements (from Phase A):**
{requirements_in_scope}

**User-clarification block (authoritative — do NOT flag gaps the user has already resolved):**
{user_clarification}

### Phase 2 — Pre-register scenarios and invariant questions (BEFORE reading the plan)

From the requirement + clarifications alone — without touching `{plan_md_path}` — derive scenarios and their invariant questions. **Emit them in your response text now, before any further tool call.** This commits the pre-registered list.

**Scenario floor** (must hit the floor; no upper cap — pick as many as the requirement warrants):

- For **behavioral requirements** (the feature changes observable behavior): ≥1 happy path + ≥1 edge case + ≥1 failure case.
- For **refactors / non-behavioral changes** (rename, type changes, internal restructure): ≥1 main-flow preservation + ≥1 caller-impact + ≥1 boundary invariant.

For each scenario, write a `**Why this scenario:**` justification line (one of: most-likely user flow / highest-blast-radius failure / boundary condition / etc.).

For each scenario, write **3–7 invariant questions** in interrogative form. Examples:
- Behavioral (P2P transfer happy path): *"Is the sender's balance reduced by exactly the transfer amount? Is the receiver credited the same amount? Is a transaction record created naming both account IDs? Is the operation atomic on partial failure?"*
- Behavioral (P2P concurrent edge): *"If two transfers from the same sender land in the same instant, are both reflected with no lost update?"*
- Refactor (rename helper across the codebase): *"Does the plan touch every existing caller? Do call sites have identical observable behavior before and after? Is no consumer left holding the old name?"*

**Question rules:**
- **Observable / externally verifiable only.** Ask about behavior a user or downstream system would notice. Do NOT ask about internal implementation choices (which data structure, which hook, which framework flag) — that is the executor's domain.
- **Flow-level is allowed.** A question may span multiple requirements or a whole flow (e.g., *"Does the plan keep the transfer atomic across the credit and debit tasks?"*). Questions do NOT need 1:1 mapping to scope bullets — the Trace handles that.
- **Decision-forcing.** Each question must be answerable as "yes, here's the evidence" / "weak, here's what's nearby" / "no, missing." Open-ended questions are not allowed.

**Stop rule.** If a question would require reading source code to verify a type literal, exact name, transform shape, or framework flag — you have drifted into execute-time territory. Rewrite it at the observable level. If you genuinely cannot, surface it as `implementation_in_plan` in Escalations.

### Phase 3 — NOW read the plan

Issue this Read call:
- `{plan_md_path}` — the whole plan. Sections you will use: `## Scope`, `## Capabilities`, `## Per-Capability Analysis & Approach Selection`, `## Component Notes`, `## Phases`, `## Tasks` (per-phase tables with `Done when`, `Provides`, `Needs` columns), `## Composition Audit` (table with Status/Notes).

Your pre-registered questions are already committed in the response above. They do not change based on what you find in the plan.

### Phase 4 — Requirement Satisfaction Trace

One row per in-scope requirement. For each requirement, trace through the plan to find the tasks that, together, deliver it. The trace stays at the level of "which tasks contribute" — do NOT verify implementation details. Produce:

- **Plan Path** — comma-separated tasks (e.g., `Ph1 / task-02 (Add CSV serializer) → Ph2 / task-01 (Wire serializer into endpoint)`)
- **Artifact After Plan Completes** — the user-visible / system-visible outcome that exists once all listed tasks complete. State the capability, not the implementation.
- **Verdict** — `DEMONSTRABLY_SATISFIED` (listed tasks deliver the capability when read as outcomes; no gap requires reading source to disprove) / `PARTIALLY_SATISFIED` (a sub-step is missing — name it) / `NOT_SATISFIED` (no task delivers this requirement).
- **Gap** — required for non-DEMONSTRABLY_SATISFIED. State the missing **capability**, not the missing detail.

### Phase 5 — Verdict the pre-registered scenario questions against the plan

For each question from Phase 2 (in order, scenario by scenario): find the **plan element(s)** that evidence it.

- **Evidence may be a combination.** A single task, multiple tasks across phases, a task plus an audit row, or a task plus a `Provides`/`Needs` interface — cite ALL relevant elements together (e.g., `Ph1 / task-02 + Ph2 / task-01 + audit #3`). Flow-level invariants typically require multi-element evidence; that is expected.
- **Verdicts:**
  - `EVIDENCED` — the cited plan elements collectively deliver the invariant. The trail from setup to invariant-holding outcome is concrete.
  - `WEAK` — the plan elements touch the area but don't collectively state this invariant. Cite what's nearby and name the gap.
  - `MISSING` — no plan element delivers this invariant. Cite `—` and name what's missing.
- **Per-scenario verdict:** `PASS` (all questions `EVIDENCED`) / `NEEDS_REVISION` (any `MISSING` or `WEAK`) / `AMBIGUOUS` (a question can't be evaluated without further clarification — surface in Escalations).

### Phase 6 — Severity

- `PASS` — every Trace row `DEMONSTRABLY_SATISFIED` AND every Scenario `PASS`.
- `FAIL_REVISION_NEEDED` — any Trace row non-satisfied, OR any Scenario `NEEDS_REVISION` (i.e., any `MISSING` or `WEAK` evidence anywhere). Per orchestrator policy, MISSING/WEAK always forces a plan revision round — never auto-accepted.
- `FAIL_AMBIGUOUS` — any row or scenario `AMBIGUOUS`.

When uncertain between PASS and FAIL_REVISION_NEEDED, choose FAIL_REVISION_NEEDED — surfacing a false positive is cheap; missing a real feasibility gap is expensive.

**Rules across all rows:**
- Every claim cites a specific plan element (task, phase, audit row, file in `§component-notes`, decision row in `§analysis`). No vague claims.
- The user-clarification block is authoritative. Do NOT flag gaps the user has already resolved.

### Phase 7 — Output in this exact format

```
## Status
**Result:** PASS | FAIL_REVISION_NEEDED | FAIL_AMBIGUOUS
**Trace_Pass_Count:** {N}/{Total}
**Scenarios_Passed:** {N}/{Total}
**Missing_Evidence:** {count of MISSING + WEAK across all scenarios}

## Requirement Satisfaction Trace
| Requirement | Plan Path | Artifact After Plan Completes | Verdict | Gap |
|-------------|-----------|------------------------------|---------|-----|
| {requirement text} | {plan elements} | {concrete artifact} | DEMONSTRABLY_SATISFIED ∣ PARTIALLY_SATISFIED ∣ NOT_SATISFIED | {gap or —} |

## Scenario Walkthrough

### Scenario 1: {name} — {happy ∣ edge ∣ failure ∣ main-flow-preservation ∣ caller-impact ∣ boundary}
**Why this scenario:** {one-line justification}
**Setup:** {the concrete situation in domain terms}

**Invariants (must hold after plan executes):**
| # | Question | Evidence (plan elements — may cite multiple) | Verdict |
|---|----------|----------------------------------------------|---------|
| 1 | {question} | `Ph<X> / task-NN` + `Ph<Y> / task-MM` + audit #K (or `—`) | EVIDENCED ∣ WEAK ∣ MISSING |
| 2 | ... | ... | ... |

**Scenario Verdict:** PASS ∣ NEEDS_REVISION ∣ AMBIGUOUS

### Scenario 2: ...

## Escalations
| Type | Description |
|------|-------------|
| {clarification_conflict ∣ ambiguous_requirement ∣ external_unknown ∣ implementation_in_plan} | {details with citation} |
```

**Format rules:**
- **Result:** exact enum string from the three options.
- **Trace_Pass_Count:** integer N (`DEMONSTRABLY_SATISFIED` count) over integer Total (total in-scope requirements).
- **Scenarios_Passed:** integer N (Scenario `PASS` count) over integer Total (total scenarios you ran).
- **Missing_Evidence:** integer count of `MISSING` + `WEAK` cells across all scenario invariant tables.
- **Requirement Satisfaction Trace:** one row per in-scope requirement, no exceptions.
- **Scenario Walkthrough:** every scenario you pre-registered in Phase 2 appears here with its Setup, Invariants table, and Scenario Verdict — no fewer, no more.
- **Escalations:** write `| None | None |` if none apply; never omit the section.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: PASS ∣ FAIL_REVISION_NEEDED ∣ FAIL_AMBIGUOUS | Decide: accept, revise, or escalate |
| | `**Trace_Pass_Count**`: N/Total; `**Scenarios_Passed**`: N/Total; `**Missing_Evidence**`: int | Coverage + depth gauge |
| `## Requirement Satisfaction Trace` | `Requirement`, `Plan Path`, `Artifact After Plan Completes`, `Verdict`, `Gap` | For each non-DEMONSTRABLY_SATISFIED verdict: Edit `§tasks` to close the Gap |
| `## Scenario Walkthrough` | Per scenario: name, classification, `Why`, `Setup`, Invariants table (`Question`, `Evidence`, `Verdict`), `Scenario Verdict` | For each `MISSING` or `WEAK` invariant: Edit `§tasks` (or `§phases` / `§analysis` if structural) to add or strengthen a task whose `Done when` delivers the invariant. Then re-spawn. |
| `## Escalations` | Type, Description | If any rows: present to user before continuing |

**Orchestrator action by Result:**
- `PASS` → paste the Trace + Scenario Walkthrough verbatim into the `## Feasibility` section of `plan.md`; fold any open or `WEAK`-mitigation notes into `## Risks`; proceed to Step 11.
- `FAIL_REVISION_NEEDED` → for each non-satisfied Trace row AND for each `MISSING`/`WEAK` invariant, Edit the affected sections of `plan.md` (`§tasks` most often; `§phases` or `§analysis` if the gap is structural). Re-spawn the subagent (**max 2 revision rounds total**). If still failing after 2 rounds, present findings to the user and ask how to proceed.
- `FAIL_AMBIGUOUS` → present Escalations to the user; on receiving clarification, update the inline `{user_clarification}` block and re-spawn.

Escalation type meanings: `clarification_conflict` (clarification block contradicts the plan), `ambiguous_requirement` (an in-scope item can't be evaluated), `external_unknown` (depends on an unverified external system), `implementation_in_plan` (a `Done when` prescribes HOW — rewrite it as an outcome before proceeding).
