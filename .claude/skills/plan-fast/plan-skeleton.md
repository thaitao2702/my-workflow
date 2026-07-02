<!-- §meta -->
# Plan: {Plan Name}

**Created:** {YYYY-MM-DD}
**Status:** draft
**Note:** Markdown plan — not runnable by the execution skill (no JSON artifacts).
<!-- /§meta -->

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

<!-- §feasibility -->
## Grounding & Coverage

**Grounding:** [N concretes verified, M corrected, D deferred — 0 invented remaining]

| Requirement | Delivering Task(s) | Covered |
|-------------|--------------------|---------|
| [requirement] | Ph1/task-02 → Ph2/task-01 | yes |
<!-- /§feasibility -->

<!-- §risks -->
## Risks

- [risk] — [1-line mitigation]
<!-- /§risks -->
