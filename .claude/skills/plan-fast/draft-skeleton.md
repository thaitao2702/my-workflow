<!-- §meta -->
# Plan Draft: {Plan Name}

**Created:** {YYYY-MM-DD}
**Status:** draft
**Final plan:** sibling `plan.md` — materialized at Step 10 from this draft
**Purpose:** working artifact + audit trail. Holds clarification log, decision classifications, rejected approach evaluations, composition audit, and the full feasibility output. Frozen at Step 11 with a `[FROZEN at approval — {YYYY-MM-DD}]` marker; never edited after that.
<!-- /§meta -->

<!-- §self-check -->
## Self-Check Findings (Step 2 — gap analysis)

| Gap Category | Concrete Gap Identified | Generated Question (or "None") |
|--------------|------------------------|-------------------------------|
| Implicit requirements (auth, validation, error handling, idempotency, rate limiting, audit logging, localization) | | |
| Data sources / dependencies / external systems | | |
| Unhappy paths / edge cases (invalid input, dependency down, concurrent action, partial failure, boundary values) | | |
| Scope boundaries (what's explicitly NOT included — adjacent capabilities and stretch features) | | |
<!-- /§self-check -->

<!-- §clarification-log -->
## Clarification Log

*One sub-section per round. Capture the question asked, the user's verbatim answer, and any constraint that emerges. Empty if the Self-Check found no gaps and clarification was skipped.*

### Round 1
- **Q:** [question]
- **A:** [user's answer]
- **Constraint locked:** [the durable constraint this answer creates, in one line]
<!-- /§clarification-log -->

<!-- §scope -->
## Scope

**In scope:**
- [confirmed requirement]

**Out of scope:**
- [explicit exclusion]
<!-- /§scope -->

<!-- §capabilities -->
## Capabilities

1. [Capability name] — [what it delivers, one line]
2. ...
<!-- /§capabilities -->

<!-- §analysis -->
## Per-Capability Analysis & Approach Selection

### Capability 1: [Name]
**Core problem:** [the actual technical challenge, 1-2 sentences]

**Decisions:**
| Decision | Classification | Cascade Trace | Rationale |
|----------|---------------|---------------|-----------|
| [decision] | Constrained ∣ Conventional ∣ Significant | [does this choice change phase structure, add tasks, or alter dependencies? Trace explicitly — "None — purely local" only after the trace] | [why this classification] |

[IF significant decisions exist:]
**Approach evaluation: [decision]**
| Approach | What | Key Trade-off | Fit |
|----------|------|---------------|-----|

**Selected:** [approach] — [1-line rationale]
**Committed approach:** [1-line summary of how this capability is built]
<!-- /§analysis -->

<!-- §component-notes -->
## Component Notes

- `path/to/file`: [constraint or hidden behavior that shapes the plan]
<!-- /§component-notes -->

<!-- §phases -->
## Phases

- **Phase 1: [Name]** (Execution Group A) — Capabilities: [1, 3] — depends on: none
- **Phase 2: [Name]** (Execution Group B) — Capabilities: [2] — depends on: Phase 1
<!-- /§phases -->

<!-- §tasks -->
## Tasks

### Phase 1: [Name] (Execution Group A)
| Task ID | Name | Capability | Files | Provides | Needs | Done when (outcome, WHAT not HOW) |
|---------|------|-----------|-------|----------|-------|-----------------------------------|
| task-01 | [name] | [Cap N] | `path/one.ts`, `path/two.ts [new]` | contract-01: [name] — [one-line behavioral semantic] ∣ — | — | [observable outcome in one sentence] |

### Phase 2: [Name] (Execution Group B)
| Task ID | Name | Capability | Files | Provides | Needs | Done when (outcome, WHAT not HOW) |
|---------|------|-----------|-------|----------|-------|-----------------------------------|
| task-01 | [name] | [Cap N] | `path/three.ts` | — | Ph1 contract-01 | [observable outcome in one sentence] |
<!-- /§tasks -->

<!-- §audit -->
## Composition Audit

| # | Concern Type | Subject | Producer / Source | Consumer / Target | Status | Notes |
|---|--------------|---------|-------------------|-------------------|--------|-------|
<!-- /§audit -->

<!-- §feasibility-full -->
## Feasibility — Full Output (subagent verbatim)

*Pre-registered scenario questions (Phase 2 of the feasibility prompt) appear first, then the verdicts (Phase 5). The pre-registration ordering is part of the audit trail.*

[Trace + Scenario Walkthrough — pasted verbatim from the feasibility subagent. Includes the Status block, Requirement Satisfaction Trace, every Scenario with its Setup + invariant questions + evidence verdicts, and Escalations.]
<!-- /§feasibility-full -->

<!-- §risks -->
## Risks

- [risk] — [1-line mitigation]
<!-- /§risks -->

<!-- §direction-summary -->
## Direction Summary (Step 10 — what the user approved)

*Snapshot of what was presented at the user checkpoint. Filled at Step 10 after user approval; not edited after.*

- **Approved:** {YYYY-MM-DD}
- **Capability list confirmed:** [list]
- **Key decisions accepted:** [significant decisions table reference]
- **Feasibility result accepted:** PASS / accepted-as-revised / etc.
- **Outstanding ACCEPTED RISKs the user explicitly accepted:** [list, or "None"]
<!-- /§direction-summary -->
