---
description: |
  Speed-optimized planning skill that keeps decomposition rigor but strips the
  heavy machinery. Produces a single human-readable markdown plan through
  requirement clarification, EARLY capability confirmation, parallel codebase
  discovery, per-capability approach analysis, phase/task drafting with a
  composition audit, and an independent feasibility subagent — then one user
  checkpoint. No JSON schemas, no acceptance/test specs, no analysis-doc reads,
  no multi-dimension plan review.

  Accepts requirements from text, file path, GitHub issue, GitLab issue, or
  Jira ticket — invokes the matching skill to fetch external sources.

  Triggers: "/plan-fast [requirement]", "fast plan", "quick rigorous plan",
  "speed plan with capabilities", "plan fast from gh / gl / jira",
  "plan this quickly but show me the capabilities first".

  Use when you want capability-level rigor and an objective feasibility check
  without the full review pipeline. Skip when you need machine-readable
  executable plan files (use the full planning skill) or a zero-ceremony
  bare-bones markdown plan (use the lightweight planning skill).
---

# /plan-fast — Fast Markdown Plan with Capability Rigor

You are producing a focused, human-readable execution plan as a single markdown file. The plan keeps the reasoning that prevents directional mistakes — requirement clarification, capability decomposition, per-capability approach selection, a cross-phase composition audit, and an independent feasibility check — while dropping JSON materialization, acceptance/test specs, and the 13-dimension review. Speed comes from confirming capabilities with the user EARLY (before deep design), parallelizing codebase discovery, and a single user checkpoint.

**Input:** `/plan-fast "text"`, `/plan-fast ./path/to/file.md`, `/plan-fast gh:123`, `/plan-fast gl:456`, `/plan-fast jira:PROJ-789`
**Output:** `.workflow/plans/{YYMMDD}-{slug}/plan.md` — a markdown plan. It is NOT consumed by the execution skill; it is for human reading, manual execution, or discussion.

## Expert Vocabulary Payload

**Decomposition:** capability (MECE functional unit), decision classification (constrained / conventional / significant), cascade trace, decide-then-descend, approach evaluation, committed approach

**Composition:** execution group (parallel-safe), phase grouping, transition (runtime data/control flow), external consumer (interface change with outside callers), group ordering (producer before consumer), composition audit, remediation

**Validation:** requirement satisfaction trace, premortem, author-bias separation, capability coverage (WHAT not HOW), executor-source test

## Anti-Pattern Watchlist

### Skipping early capability confirmation
- **Detection:** Decomposing into capabilities and then proceeding straight to approach analysis or phase design without pausing for the user to confirm the capability list.
- **Resolution:** Step 3 is a hard stop. The confirmed capability list is the contract for everything after it. Catching a wrong capability here costs one message; catching it after the full plan is written costs a rewrite.

### Defining the skill by negation
- **Detection:** Treating "no analysis docs" or "no tests" as steps to perform ("check that no analysis doc is read"). This skill simply has no such machinery — there is nothing to suppress.
- **Resolution:** Do the positive action: discovery reads the project overview and runs targeted Explore agents. Absence of the dropped machinery is structural, not a checklist item.

### Full-file rewrite of plan.md
- **Detection:** Using the Write tool on `plan.md` after the Step 4 skeleton exists, or regenerating untouched sections while editing one.
- **Resolution:** After the skeleton is created, every change is **Read `plan.md` → Edit exactly one tagged block**. Untouched sections must remain byte-identical — that is the determinism guarantee. Regenerating the whole file lets confirmed sections silently drift.

### Performative composition audit
- **Detection:** Filling the Step 8 audit table with rows that describe a concern but produce no edit to the `§phases`/`§tasks` blocks.
- **Resolution:** Every audit row whose concern requires a plan change must drive a concrete tagged-block Edit BEFORE the next row, or be escalated to the user. A table that only describes is bureaucracy.

### Over-specified task drafts
- **Detection:** A `Done when` cell that prescribes HOW — URLs, body schemas, exact symbol names, hook names, internal data structures.
- **Resolution:** `Done when` states an observable outcome that did not exist before the task. Apply the executor-source test: "Reading this as the executor, will I still need to read source to figure out HOW?" If yes, you over-specified — rewrite as an outcome.

### Author-biased feasibility
- **Detection:** Running the feasibility trace/premortem yourself in the main session because it is faster.
- **Resolution:** The feasibility check runs as a separate-context subagent. You designed the plan, so your judgment of "would this work?" inherits your blind spots. The subagent reads it fresh.

### Ad-hoc contract block
- **Detection:** Writing a freeform "Shared contract", "Interface agreement", or similar prose paragraph anywhere in `plan.md` to describe a cross-phase dependency, instead of using the `Provides`/`Needs` task columns.
- **Resolution:** The two columns are the single authoritative cross-phase interface record. Put the producer semantic in `Provides` and the reference in the consumer's `Needs`. A prose block duplicates the fact in a place the executor does not read — delete it and use the columns.

## Plan File Structure & Editing Discipline

`plan.md` is a clean human-readable markdown document whose sections are delimited by **HTML-comment tags**. HTML comments render invisibly, so the document stays readable, while the tag pairs are permanent, uniquely-addressable anchors.

**The skeleton is written once** (Step 4) with every tag pair present and bodies empty except the ones filled by then. **Every subsequent write or revision is a tagged-block Edit:**

> Read `plan.md` → Edit, replacing the entire `<!-- §name -->` … `<!-- /§name -->` block (delimiters included) with the rebuilt block. Change exactly one block per Edit. Never use the Write tool on `plan.md` after the skeleton exists.

This is deterministic because the tag pair never disappears (unlike a consumed placeholder) and the delimiter names make each block a unique `old_string`; sections you do not touch are preserved byte-for-byte.

Skeleton written at Step 4:

```markdown
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
## Feasibility

[Requirement Satisfaction Trace + Premortem — pasted verbatim from the feasibility subagent]
<!-- /§feasibility -->

<!-- §risks -->
## Risks

- [risk] — [1-line mitigation]
<!-- /§risks -->
```

---

## Phase A: Requirement Gathering & Capability Confirmation

### Step 1: Parse Input

| Input Pattern | Action |
|--------------|--------|
| `"quoted text"` or plain text | Use directly as the initial requirement |
| `./path/to/file.md` | Read the file, extract the initial requirement |
| `gh:123` or GitHub URL | Use the Skill tool to invoke `/github` with the issue reference |
| `gl:123` or GitLab URL | Use the Skill tool to invoke `/gitlab` with the issue reference |
| `jira:PROJ-456` | Use the Skill tool to invoke `/jira` with the ticket ID |

The skill invocations return issue/ticket content as clean markdown. Treat it as the starting requirement text.

### Step 2: Clarification

Ground the requirement before decomposing it.

1. Read `.workflow/project-overview.md` for architectural context. If it doesn't exist, note that and proceed.

2. **Self-check before generating questions.** Output this table — every row filled (use "None identified" only after genuine analysis):

   **Self-Check Findings:**
   | Gap Category | Concrete Gap Identified | Generated Question (or "None") |
   |--------------|------------------------|-------------------------------|
   | Implicit requirements (auth, validation, error handling, permissions) | | |
   | Data sources / dependencies / external systems | | |
   | Unhappy paths / edge cases | | |
   | Scope boundaries (what's explicitly NOT included) | | |

3. Generate questions from the "Generated Question" column. Phrasing rule:
   - Specific and decision-forcing: "When payment validation fails on POST /orders, should the order persist as 'pending' or be discarded?" — good
   - NOT open-ended: "Tell me more about the requirements" — bad

4. Present questions, wait for answers. Loop until no genuine gaps remain (max 3 rounds). Re-output the Self-Check table each new round with updated rows.

5. If every row is "None identified" — requirements are clear — skip the question rounds but still produce the consolidated requirement statement in Step 3.

Maintain a running **clarification block** in the conversation (every answer and constraint the user gave) — Step 9 passes it to the feasibility subagent.

### Step 3: Capability Decomposition + User Confirmation

Decompose the consolidated requirement into capabilities and **confirm them with the user before any deeper design**.

Rules:
- Each capability is an independent functional unit delivering user-visible or system-visible value.
- MECE — no overlaps, no gaps. Each capability is one sentence.
- Not everything decomposes — a requirement mapping to one obvious capability is fine.
- More than 7 → group related ones into domains first.

Present to the user:

> "Here are the capabilities I'll plan around:
> 1. [Capability] — [one line]
> 2. ...
>
> Confirm or correct before I design the approach."

Wait for explicit confirmation. Apply corrections and re-present until confirmed. **The confirmed capability list is the contract for the rest of the run** — later steps may not silently add or drop capabilities; a change requires returning here.

### Step 4: Initialize Plan Directory

- Derive a kebab-case `{slug}` from the requirement (e.g., "Add CSV export to orders API" → `add-csv-export-orders-api`)
- Compute `$PLAN_DIR = .workflow/plans/{YYMMDD}-{slug}/` where `{YYMMDD}` is today's date
- Create the directory
- **Write the full tagged skeleton** (the structure above) to `$PLAN_DIR/plan.md` with the Write tool — once. Fill `§meta` (name, today's date, Status `draft`), `§scope` (in/out from Steps 2–3), and `§capabilities` (the confirmed list). Leave all other tagged bodies as their placeholder text. This is the only Write to this file; from here on, every change is a Read → tagged-block Edit.

State: "Wrote tagged skeleton with Scope + {N} confirmed capabilities to $PLAN_DIR/plan.md."

## Phase B: Parallel Discovery

### Step 5: Frame Discovery Subjects

Using the confirmed capabilities + `.workflow/project-overview.md` as the map, list 1–3 **discovery subjects**. Each subject is a single self-contained question whose answer shapes the plan — e.g., "How is the orders API module structured, and what pattern do existing export-style endpoints follow?" or "Where does request validation run for write endpoints, and how is it registered?"

Aim for the fewest subjects that cover the uncertain surface area. One subject is fine for an isolated change.

### Step 6: Spawn Explore Agents in Parallel

Spawn one `Explore` subagent per subject — **all in a single message (multiple Agent tool calls)** so they run concurrently. Each prompt:
- States exactly one discovery subject
- Asks for conclusions and the specific constraints / patterns / integration points found (file path + line where it matters), not file dumps
- Specifies the search breadth ("medium" for a focused subject, "very thorough" if the subject spans multiple modules)

Collect the returned findings. Read `plan.md` and Edit the `§component-notes` block — one bullet per concrete constraint or pattern that shapes a phase, task, or approach (cite `path:line`).

State: "Discovery complete ({N} subjects) — {M} component notes written."

## Phase C: Plan Creation

### Step 7: Per-Capability Analysis & Approach Selection

Process the confirmed capabilities **one at a time**. For each, decide before descending to the next — no open options carried forward.

**Decision classification** (apply to every decision):
- **Constrained** — the project/codebase already dictates the choice (existing framework, established pattern). No alternatives generated.
- **Conventional** — one obvious best practice; no real branch.
- **Significant** — viable alternatives exist AND the choice is hard to reverse AND it cascades into phase/task/dependency structure. Only these get an approach evaluation (≤3 approaches).
- **Cascade Trace is mandatory for every decision** — trace whether the choice changes phase structure, adds tasks, or alters dependencies. "None — purely local" is valid only after an explicit trace. A choice that cascades is Significant regardless of how obvious it seems.

Complexity gate: if a capability has one obvious constrained/conventional approach, collapse its block to **Core problem** + **Committed approach** (skip the tables).

Read `plan.md` and Edit the `§analysis` block, writing one per-capability sub-block (format in the skeleton). Every sub-block ends with `**Selected:**` (if significant) and `**Committed approach:**`.

State: "Wrote per-capability analysis for {N} capabilities."

### Step 8: Phase Grouping, Task Drafts & Composition Audit

Produce each part, then apply it as a tagged-block Edit.

**8.1 — Phase grouping.** Group capabilities into phases by cohesion and dependency order. Assign each phase an execution group (A, B, …). Phases in the same group run in parallel and MUST NOT modify the same files. A single capability may span phases if it has natural sequential stages. Read `plan.md`, Edit the `§phases` block.

**8.2 — Task drafts.** Per phase, draft the task table:
- Each task is a coherent unit of work (≈ one commit's worth). Trivial 1–2 line standalone changes merge into a related task.
- Task IDs `task-01`, `task-02`, … reset per phase.
- Files are concrete paths from Step 6 discovery; mark non-existent paths `[new]`.
- **`Done when` is ONE sentence describing an observable outcome** — a function/file/endpoint/UI element/behavior that exists after the task and did not before. State the user- or system-visible result; do NOT describe the steps. Apply the executor-source test.
- **`Provides` and `Needs` start as `—`.** They are filled in Step 8.3 when cross-phase dependencies are identified — do not guess them now.
- No acceptance criteria, no test requirements — those are deliberately out of this skill.

Edit the `§tasks` block.

**8.3 — Composition audit.** With phases and tasks committed, surface cross-phase concerns. Concern types:
- **Transition** — a runtime control/data flow between phases. Every user-action → system-response path must be covered by Transition rows; a missing one is a plan gap.
- **External Consumer** — a task modifies an existing interface (signature, return type, props, API contract, schema, event payload) that code outside the plan may call. Grep for consumers of the *specific* interface.
- **Group Ordering** — the producer phase's execution group must be strictly earlier than every consumer phase's; no cycles.

**Cross-phase interface contracts (fill the `Provides`/`Needs` columns — this is the ONLY cross-phase interface record).** For every cross-phase code dependency the Group Ordering analysis surfaces (a task in Phase Y imports, calls, or receives an object created by a task in Phase X):
- On the **producer** task (Phase X) set `Provides` to `contract-NN: <name> — <one-line behavioral semantic>`. `NN` is sequential **within the producing phase** (`contract-01`, `contract-02`, …). The semantic is WHAT a consumer can rely on (purpose + what it returns/does), never a type literal or signature — the realized signature is filled later by the executor in `progress.md`, not here.
- On every **consumer** task (Phase Y) set `Needs` to `Ph<X> contract-NN`.
- Fill `Provides` ONLY when at least one task's `Needs` references it. A task with no cross-phase consumer keeps `Provides = —`. Internal helpers within a single phase are never contracts.
- These two columns replace any prose dependency note. Do NOT write a freeform "Shared contract" paragraph or any other ad-hoc dependency block anywhere in the plan — the columns are authoritative.

**Remediation rule.** For every audit row whose concern requires a plan change, apply the tagged-block Edit BEFORE the next row:
- Transition gap → Edit `§tasks`, add a wiring task row to the relevant phase
- External Consumer needing update → Edit `§tasks`, add a task row to the phase owning the consumer surface
- Group Ordering violation → Edit `§phases` to move the phase to a later group, and Edit `§tasks` to update its `(Execution Group X)` label
- Cross-phase dependency identified → Edit `§tasks` to set the producer task's `Provides` and the consumer task's `Needs` (per the contract rule above)
- Circular dependency → Edit `§phases` and `§tasks` to merge the phases or extract the shared piece into a new earlier phase

Then fill the row's `Notes` with the change made and set `Status` to `OK`. Re-check any row the edit affected.

**Escalation when stuck.** If a row's required change can't be applied in one pass (it would violate a user clarification or needs structural redesign), set `Status` to `ESCALATED` and present to the user:

> "Audit row #N could not be resolved:
> - **Concern:** [subject]
> - **Proposed change:** [what you tried]
> - **Blocker:** [why it can't be applied autonomously]
>
> Choose: (1) apply a manual edit you describe, (2) specify a different change, (3) accept the gap as a risk with rationale (recorded in Notes, Status → OK)."

Do not proceed to Step 9 until every audit row is `Status = OK`. Edit the `§audit` block (build the table incrementally with the same tagged-block Edit each time it changes).

State: "Wrote {P} phases, {T} tasks, audit with {R} rows (all OK)."

### Step 9: Feasibility Walkthrough (subagent — separate context)

Validate the plan with an independent reader before showing it to the user. This catches feasibility gaps your author bias hides.

**9.1 — Pre-flight.** Read `plan.md`. Confirm `§scope`, `§capabilities`, `§analysis`, `§phases`, `§tasks`, `§audit` have real content (not skeleton placeholder text) and every audit row is `OK`. If not, return to the owning step.

**9.2 — Spawn.** Read the prompt template `.claude/skills/plan-fast/feasibility-prompt.md`. Per its **For Orchestrator — Data to Collect** section, collect the data items (the `plan.md` path; the in-scope requirements as an inline bulleted list; the clarification block as an inline bulleted list). Fill the `{placeholders}` in **For Subagent — Prompt to Pass**. Spawn the **feasibility-validator** subagent (`.claude/agents/feasibility-validator.md`, read-only) **in foreground**, passing the filled "For Subagent" section as the prompt.

**9.3 — Parse & apply** per the template's **For Orchestrator — Expected Output**:
- **`PASS`** → Edit the `§feasibility` block with the subagent's Requirement Satisfaction Trace + Premortem verbatim; Edit the `§risks` block to reflect premortem mitigations/ACCEPTED RISKs; proceed to Step 10.
- **`FAIL_REVISION_NEEDED`** → for each non-satisfied trace row or plan-changing premortem mitigation, Edit the affected `§tasks`/`§phases`/`§analysis` block, then re-spawn (**max 2 revision rounds total**). If still failing after 2 rounds, present findings to the user and ask how to proceed.
- **`FAIL_AMBIGUOUS`** → present the Escalations table to the user, get answers, update the clarification block, re-spawn.

State: "Feasibility: {Result} — trace {N}/{Total} satisfied."

## Phase D: Checkpoint & Finalize

### Step 10: Direction Summary & User Checkpoint

The user understands intent better than any agent — this single checkpoint is the only human review this skill has. Present, in one message:

- Plan name + scope
- The confirmed capability list
- Per-capability **Selected/Committed** lines (significant decisions as a small table: Decision | Options | Selected | Rationale)
- Phase/group overview with dependencies
- **Main flow diagram** — a runtime arrow flow (not build order) showing how the assembled pieces connect, each step labelled with the phase that produces it. Example: `User Action → API Endpoint (Ph2) → Permission Check (Ph2) → CSV Serializer (Ph1) → Stream Response (Ph2)`. A transition no phase covers is a visible gap.
- The feasibility subagent's Requirement Satisfaction Trace + Premortem verbatim
- Top risks

Ask: "Approve to finalize, or tell me what to change."

On change requests, re-enter only the affected step (apply changes via tagged-block Edit):
- Disagreement with a capability → Step 3 (re-confirm), then ripple forward
- Disagreement with an approach → Step 7 for that capability only
- Structural change (phases/tasks/grouping) → Step 8 (regroup / redraft / re-audit)
- Reject an ACCEPTED RISK or want a premortem risk handled differently → Edit the relevant `plan.md` block and re-spawn the feasibility subagent (Step 9)

Re-present until approved.

### Step 11: Finalize

The assembled `plan.md` now contains every piece of context — capabilities, approaches, phases, tasks, audit, feasibility. Use it as the single source of truth for the final consistency pass.

1. **Read the full `plan.md`** end to end. Self-verify cross-section coherence:
   - Every confirmed capability is delivered by ≥1 task in `§tasks`
   - Every `§phases` group ordering is consistent with the `§audit` Group Ordering rows
   - The feasibility trace in `§feasibility` matches the current `§tasks` (no row references a task that was later edited away)
   - **Interface integrity:** every `Needs` cell `Ph<X> contract-NN` resolves to exactly one task whose `Provides` declares that `contract-NN` in Phase X, and that producing phase's execution group is strictly earlier than the consumer's; every `Provides` is referenced by at least one `Needs` (an unconsumed contract is over-declaration — clear it to `—`)
   - `§risks` reflects the premortem outcomes
   If any inconsistency is found, fix it with a single tagged-block Edit and re-Read to confirm.
2. Edit the `§meta` block: change `**Status:** draft` → `**Status:** approved`.
3. Tell the user: "Plan approved at `$PLAN_DIR/plan.md`. Run the fast execution skill (`/execute-fast`) to implement it — it tracks progress and realized interfaces in `$PLAN_DIR/progress.md` without modifying this plan."

## Questions This Skill Answers

- "/plan-fast [requirement]"
- "Plan this fast but show me the capabilities first"
- "Quick plan with real capability analysis, no JSON"
- "Fast plan from gh:123 / gl:456 / jira:PROJ-789"
- "I want decomposition rigor without the full review pipeline"
