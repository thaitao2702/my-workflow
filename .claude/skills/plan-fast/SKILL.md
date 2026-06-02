---
description: |
  Speed-optimized planning skill that keeps decomposition rigor but strips the
  heavy machinery. Produces TWO files in `$PLAN_DIR`: `draft.md` (full working
  artifact + audit trail — clarification log, decision classifications, rejected
  approach evaluations, composition audit, full feasibility output) and
  `plan.md` (distilled final artifact — what the executor reads). draft.md is
  built incrementally via tagged-block Edits across Steps 1–9; plan.md is
  materialized at Step 10 by distilling draft.md and frozen at Step 11.

  Flow: requirement clarification, EARLY capability confirmation, parallel
  codebase discovery, per-capability approach analysis, phase/task drafting
  with a composition audit, and an independent feasibility subagent — then a
  user checkpoint where plan.md is written to disk for review. No JSON, no
  acceptance/test specs, no analysis-doc reads, no multi-dimension plan review.

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

You are producing a focused, human-readable execution plan as two markdown files. `draft.md` is your **working artifact and audit trail** — everything goes there as you plan, edited section by section via tagged-block discipline. `plan.md` is the **distilled final artifact** the executor (and human readers) consume — materialized once at Step 10 by selecting what's needed for execution from draft.md, and frozen at Step 11.

Speed comes from: confirming capabilities with the user EARLY (before deep design), parallelizing codebase discovery, a single materialization step, and only one user checkpoint.

**Input:** `/plan-fast "text"`, `/plan-fast ./path/to/file.md`, `/plan-fast gh:123`, `/plan-fast gl:456`, `/plan-fast jira:PROJ-789`
**Output:** `.workflow/plans/{YYMMDD}-{slug}/plan.md` (final, executor input — run with `/execute-fast`) and `.workflow/plans/{YYMMDD}-{slug}/draft.md` (audit trail, frozen at approval).

## Expert Vocabulary Payload

**Decomposition:** capability (MECE functional unit), decision classification (constrained / conventional / significant), cascade trace, decide-then-descend, approach evaluation, committed approach

**Composition:** execution group (parallel-safe), phase grouping, transition (runtime data/control flow), external consumer (interface change with outside callers), group ordering (producer before consumer), composition audit, remediation

**Validation:** requirement satisfaction trace, scenario walkthrough (pre-registered invariant questions, multi-element evidence, EVIDENCED/WEAK/MISSING verdicts), author-bias separation, capability coverage (WHAT not HOW), executor-source test

**Artifacts:** draft.md (working file, tagged-block Edits), plan.md (distilled, materialized once per iteration), distillation rules (which draft sections become which plan sections), frozen-at-approval marker

## Anti-Pattern Watchlist

### Skipping early capability confirmation
- **Detection:** Decomposing into capabilities and then proceeding straight to approach analysis or phase design without pausing for the user to confirm the capability list.
- **Resolution:** Step 3 is a hard stop. The confirmed capability list is the contract for everything after it. Catching a wrong capability here costs one message; catching it after the full plan is written costs a rewrite.

### Defining the skill by negation
- **Detection:** Treating "no analysis docs" or "no tests" as steps to perform ("check that no analysis doc is read"). This skill simply has no such machinery — there is nothing to suppress.
- **Resolution:** Do the positive action: discovery reads the project overview and runs targeted Explore agents. Absence of the dropped machinery is structural, not a checklist item.

### Full-file rewrite of draft.md
- **Detection:** Using the Write tool on `draft.md` after the Step 4 skeleton exists, or regenerating untouched sections while editing one.
- **Resolution:** After the skeleton is created, every change to draft.md is **Read `draft.md` → Edit exactly one tagged block**. Untouched sections must remain byte-identical — that is the determinism guarantee. Regenerating the whole file lets confirmed sections silently drift. (Note: `plan.md` is the opposite — it's written whole at Step 10 each iteration. The two files have different editing disciplines on purpose.)

### Editing plan.md directly
- **Detection:** Applying changes to `plan.md` to react to user feedback at Step 10, instead of editing `draft.md` and re-materializing.
- **Resolution:** `plan.md` is a *derivative* of `draft.md`. All revisions go to draft.md; plan.md is re-written from scratch at Step 10 after each draft change. Editing plan.md directly causes the two files to diverge — the audit trail no longer matches the final plan.

### Performative composition audit
- **Detection:** Filling the Step 8 audit table with rows that describe a concern but produce no edit to the `§phases`/`§tasks` blocks in draft.md.
- **Resolution:** Every audit row whose concern requires a plan change must drive a concrete tagged-block Edit on draft.md BEFORE the next row, or be escalated to the user. A table that only describes is bureaucracy.

### Over-specified task drafts
- **Detection:** A `Done when` cell that prescribes HOW — URLs, body schemas, exact symbol names, hook names, internal data structures.
- **Resolution:** `Done when` states an observable outcome that did not exist before the task. Apply the executor-source test: "Reading this as the executor, will I still need to read source to figure out HOW?" If yes, you over-specified — rewrite as an outcome.

### Author-biased feasibility
- **Detection:** Running the feasibility trace/scenario walkthrough yourself in the main session because it is faster.
- **Resolution:** The feasibility check runs as a separate-context subagent. You designed the plan, so your judgment of "would this work?" inherits your blind spots. The subagent reads it fresh.

### Ad-hoc contract block
- **Detection:** Writing a freeform "Shared contract", "Interface agreement", or similar prose paragraph anywhere in `draft.md` or `plan.md` to describe a cross-phase dependency, instead of using the `Provides`/`Needs` task columns.
- **Resolution:** The two columns are the single authoritative cross-phase interface record. Put the producer semantic in `Provides` and the reference in the consumer's `Needs`. A prose block duplicates the fact in a place the executor does not read — delete it and use the columns.

## File Structure & Editing Discipline

This skill produces **two files** in `$PLAN_DIR`:

| File | Purpose | Lifetime | Editing Discipline |
|------|---------|----------|---------------------|
| `draft.md` | Working artifact + audit trail. Holds clarification log, decision classifications, rejected approach evaluations, composition audit, full feasibility output, direction-summary snapshot. | Built incrementally across Steps 1–9. Frozen at Step 11 with `[FROZEN at approval — {YYYY-MM-DD}]`. Never edited after. | **Tagged-block Edit only.** Read draft.md → Edit one `<!-- §name -->` … `<!-- /§name -->` block, delimiters included. Never `Write` after the skeleton exists. Untouched sections byte-identical. |
| `plan.md` | Distilled final artifact. Holds scope, capabilities, distilled approach selection, component notes, phases, tasks (with Provides/Needs), risks, one-line feasibility summary. **This is what the executor reads.** | Materialized at Step 10 by composing from draft.md per distillation rules. Re-materialized each iteration if the user requests changes at Step 10. Status flipped from `draft` → `approved` at Step 11. | **Whole-file Write at Step 10** (clean re-derivation each iteration; no incremental editing). Targeted Edit at Step 11 ONLY for the `Status:` line. |

The draft.md skeleton is defined in [`draft-skeleton.md`](./draft-skeleton.md) — kept out of this file so the structure can be revised independently. Step 4 reads that file and writes it verbatim to `$PLAN_DIR/draft.md`; subsequent steps fill or revise the bodies between the `<!-- §… -->` tags via tagged-block Edits.

plan.md has no skeleton file — its shape is defined by the **distillation rules** in Step 10 (which sections to pull from draft.md, in which order, in what condensed form).

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

2. **Self-check before generating questions.** Run the analysis below — one pass per category, applying the named method — then fill the table. The four categories cover the most common gap classes in software requirements; the method tells you what to look for in each. Fill each row with a concrete gap (or `None identified` only when the category genuinely has nothing after applying the method — not as a default).

   **Method, by category:**
   - **Implicit requirements** — what a production-quality implementation would add by default but the requirement doesn't name. Enumerate: is authentication / authorization specified? Input validation rules? Error response shape and status codes? Idempotency on retries? Rate limiting? Audit logging? Localization / timezone handling? If something a senior engineer would build by default is silent in the requirement, it's a gap.
   - **Data sources / dependencies / external systems** — trace the data flow. Where does each input come from (user, request body, DB row, upstream service, cache, queue)? Where does each output go (response, DB write, event, downstream call, notification)? Which external systems / APIs / DBs / queues are touched? Are credentials, endpoints, or contracts assumed? If the requirement uses a noun ("the user's wallet", "the order record") without naming where that data lives or who owns it, it's a gap.
   - **Unhappy paths / edge cases** — invert the happy path. For each step the user or system takes, ask: what if the input is invalid, empty, zero, negative, or very large? what if a dependency is down, slow, or returns unexpected data? what about concurrent or duplicate actions on the same entity? what about partial failures (one write succeeds, the next fails)? Boundary values, race conditions, and timeout/retry behavior all count.
   - **Scope boundaries** — list adjacent capabilities someone reading the requirement might reasonably expect as part of this work. For each: is it in scope or explicitly out? Common adjacents: admin views, audit / reporting surfaces, migration of existing data, undo / rollback flows, cleanup of related stale state, feature flags, telemetry. Explicitly excluded items prevent scope creep later.

   **Quality bar for the "Concrete Gap" cell:** specific, decision-forcing — not category-restating. Compare:
   - BAD: `auth concerns` / `edge cases not covered` / `data flow unclear` — these just re-name the category.
   - GOOD: `POST /transfer has no auth spec — wallet owner only or any authenticated user with valid IDs?` / `transfer amount of 0 — silently no-op or return 400?` / `requirement says "the wallet" but the system has both custodial and self-custody wallet tables — which one?`

   The "Generated Question" cell rephrases the gap as a decision-forcing question the user can answer in one sentence.

   **Self-Check Findings:**
   | Gap Category | Concrete Gap Identified | Generated Question (or "None") |
   |--------------|------------------------|-------------------------------|
   | Implicit requirements (auth, validation, error handling, idempotency, rate limiting, audit logging, localization) | | |
   | Data sources / dependencies / external systems | | |
   | Unhappy paths / edge cases (invalid input, dependency down, concurrent action, partial failure, boundary values) | | |
   | Scope boundaries (what's explicitly NOT included — adjacent capabilities and stretch features) | | |

   *Worked example row (showing the bar):*
   | Implicit requirements | The "transfer money" endpoint has no auth spec — caller could be the wallet owner only, or any authenticated user with valid wallet IDs. | "Should the transfer endpoint be restricted to the wallet's owner, or open to any authenticated user with valid sender + receiver IDs?" |

3. Generate questions from the "Generated Question" column. Phrasing rule:
   - Specific and decision-forcing: "When payment validation fails on POST /orders, should the order persist as 'pending' or be discarded?" — good
   - NOT open-ended: "Tell me more about the requirements" — bad

4. Present questions, wait for answers. Loop until no genuine gaps remain (max 3 rounds). Re-output the Self-Check table each new round with updated rows.

5. If every row is "None identified" — requirements are clear — skip the question rounds but still produce the consolidated requirement statement in Step 3.

The Self-Check Findings table and the full Q&A log are persisted to draft.md at Step 4 (the Self-Check table to `§self-check`; every round's Q&A to `§clarification-log`). The clarification block also lives in the running conversation — Step 9 passes it inline to the feasibility subagent.

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

### Step 4: Initialize Plan Directory & draft.md

- Derive a kebab-case `{slug}` from the requirement (e.g., "Add CSV export to orders API" → `add-csv-export-orders-api`)
- Compute `$PLAN_DIR = .workflow/plans/{YYMMDD}-{slug}/` where `{YYMMDD}` is today's date
- Create the directory
- **Write the full tagged skeleton to `$PLAN_DIR/draft.md` — once.** Read `.claude/skills/plan-fast/draft-skeleton.md` and Write its content verbatim to the new file (Write tool). Then Edit the tagged blocks that are known at this point:
  - `§meta` (name, today's date, `Status: draft`)
  - `§self-check` (the Self-Check Findings table built in Step 2; if Step 2 was skipped because no gaps existed, mark each row `None identified`)
  - `§clarification-log` (every round from Step 2, with the user's verbatim answers; "None — requirements were unambiguous as written" if skipped)
  - `§scope` (in/out from Steps 2–3)
  - `§capabilities` (the confirmed list)

  Leave every other tagged body as its placeholder text. This is the only Write to `draft.md`; from here on, every change is a Read → tagged-block Edit. **Do NOT create `plan.md` yet — it is materialized at Step 10.**

State: "Wrote tagged skeleton to draft.md with Self-Check, Clarification Log, Scope, and {N} confirmed capabilities."

## Phase B: Parallel Discovery

### Step 5: Frame Discovery Subjects

Using the confirmed capabilities + `.workflow/project-overview.md` as the map, list 1–3 **discovery subjects**. Each subject is a single self-contained question whose answer shapes the plan — e.g., "How is the orders API module structured, and what pattern do existing export-style endpoints follow?" or "Where does request validation run for write endpoints, and how is it registered?"

Aim for the fewest subjects that cover the uncertain surface area. One subject is fine for an isolated change.

### Step 6: Spawn Explore Agents in Parallel

Spawn one `Explore` subagent per subject — **all in a single message (multiple Agent tool calls)** so they run concurrently. Each prompt:
- States exactly one discovery subject
- Asks for conclusions and the specific constraints / patterns / integration points found (file path + line where it matters), not file dumps
- Specifies the search breadth ("medium" for a focused subject, "very thorough" if the subject spans multiple modules)

Collect the returned findings. Read `draft.md` and Edit the `§component-notes` block — one bullet per concrete constraint or pattern that shapes a phase, task, or approach (cite `path:line`).

State: "Discovery complete ({N} subjects) — {M} component notes written to draft.md."

## Phase C: Plan Creation

### Step 7: Per-Capability Analysis & Approach Selection

Process the confirmed capabilities **one at a time**. For each, decide before descending to the next — no open options carried forward.

**Decision classification** (apply to every decision):
- **Constrained** — the project/codebase already dictates the choice (existing framework, established pattern). No alternatives generated.
- **Conventional** — one obvious best practice; no real branch.
- **Significant** — viable alternatives exist AND the choice is hard to reverse AND it cascades into phase/task/dependency structure. Only these get an approach evaluation (≤3 approaches).
- **Cascade Trace is mandatory for every decision** — trace whether the choice changes phase structure, adds tasks, or alters dependencies. "None — purely local" is valid only after an explicit trace. A choice that cascades is Significant regardless of how obvious it seems.

Complexity gate: if a capability has one obvious constrained/conventional approach, collapse its block to **Core problem** + **Committed approach** (skip the tables).

Read `draft.md` and Edit the `§analysis` block, writing one per-capability sub-block (format in the skeleton). Every sub-block ends with `**Selected:**` (if significant) and `**Committed approach:**`. Keep the Decisions table (Classification + Cascade Trace) and Approach Evaluation tables in draft.md — they are part of the audit trail. Step 10 will choose which of these survive into plan.md.

State: "Wrote per-capability analysis for {N} capabilities to draft.md."

### Step 8: Phase Grouping, Task Drafts & Composition Audit

Produce each part, then apply it as a tagged-block Edit on draft.md.

**8.1 — Phase grouping.** Group capabilities into phases by cohesion and dependency order. Assign each phase an execution group (A, B, …). Phases in the same group run in parallel and MUST NOT modify the same files. A single capability may span phases if it has natural sequential stages. Read `draft.md`, Edit the `§phases` block.

**8.2 — Task drafts.** Per phase, draft the task table:
- Each task is a coherent unit of work (≈ one commit's worth). Trivial 1–2 line standalone changes merge into a related task.
- Task IDs `task-01`, `task-02`, … reset per phase.
- Files are concrete paths from Step 6 discovery; mark non-existent paths `[new]`.
- **`Done when` is ONE sentence describing an observable outcome** — a function/file/endpoint/UI element/behavior that exists after the task and did not before. State the user- or system-visible result; do NOT describe the steps. Apply the executor-source test.
- **`Provides` and `Needs` start as `—`.** They are filled in Step 8.3 when cross-phase dependencies are identified — do not guess them now.
- No acceptance criteria, no test requirements — those are deliberately out of this skill.

Edit the `§tasks` block in draft.md.

**8.3 — Composition audit.** With phases and tasks committed, surface cross-phase concerns. Concern types:
- **Transition** — a runtime control/data flow between phases. Every user-action → system-response path must be covered by Transition rows; a missing one is a plan gap.
- **External Consumer** — a task modifies an existing interface (signature, return type, props, API contract, schema, event payload) that code outside the plan may call. Grep for consumers of the *specific* interface.
- **Group Ordering** — the producer phase's execution group must be strictly earlier than every consumer phase's; no cycles.

**Cross-phase interface contracts (fill the `Provides`/`Needs` columns — this is the ONLY cross-phase interface record).** For every cross-phase code dependency the Group Ordering analysis surfaces (a task in Phase Y imports, calls, or receives an object created by a task in Phase X):
- On the **producer** task (Phase X) set `Provides` to `contract-NN: <name> — <one-line behavioral semantic>`. `NN` is sequential **within the producing phase** (`contract-01`, `contract-02`, …). The semantic is WHAT a consumer can rely on (purpose + what it returns/does), never a type literal or signature — the realized signature is filled later by the executor in `progress.md`, not here.
- On every **consumer** task (Phase Y) set `Needs` to `Ph<X> contract-NN`.
- Fill `Provides` ONLY when at least one task's `Needs` references it. A task with no cross-phase consumer keeps `Provides = —`. Internal helpers within a single phase are never contracts.
- These two columns replace any prose dependency note. Do NOT write a freeform "Shared contract" paragraph or any other ad-hoc dependency block anywhere — the columns are authoritative.

**Remediation rule.** For every audit row whose concern requires a plan change, apply the tagged-block Edit on draft.md BEFORE the next row:
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

Do not proceed to Step 9 until every audit row is `Status = OK`. Edit the `§audit` block in draft.md.

State: "Wrote {P} phases, {T} tasks, audit with {R} rows (all OK) to draft.md."

### Step 9: Feasibility Walkthrough (subagent — separate context)

Validate the plan with an independent reader before showing it to the user. This catches feasibility gaps your author bias hides.

**9.1 — Pre-flight.** Read `draft.md`. Confirm `§scope`, `§capabilities`, `§analysis`, `§phases`, `§tasks`, `§audit` have real content (not skeleton placeholder text) and every audit row is `OK`. If not, return to the owning step.

**9.2 — Spawn.** Read the prompt template `.claude/skills/plan-fast/feasibility-prompt.md`. Per its **For Orchestrator — Data to Collect** section, collect the data items (the `draft.md` path; the in-scope requirements as an inline bulleted list; the clarification block as an inline bulleted list). Fill the `{placeholders}` in **For Subagent — Prompt to Pass**. Spawn the **feasibility-validator** subagent (`.claude/agents/feasibility-validator.md`, read-only) **in foreground**, passing the filled "For Subagent" section as the prompt.

**9.3 — Parse & apply** per the template's **For Orchestrator — Expected Output**:
- **`PASS`** → Edit the `§feasibility-full` block in draft.md with the subagent's Requirement Satisfaction Trace + Scenario Walkthrough verbatim (including the pre-registered questions, for the audit trail); Edit the `§risks` block in draft.md to reflect any unresolved scenario notes and ACCEPTED RISKs; proceed to Step 10.
- **`FAIL_REVISION_NEEDED`** → for each non-satisfied trace row AND for each `MISSING`/`WEAK` scenario invariant, Edit the affected `§tasks`/`§phases`/`§analysis` block in draft.md, then re-spawn (**max 2 revision rounds total**). If still failing after 2 rounds, present findings to the user and ask how to proceed.
- **`FAIL_AMBIGUOUS`** → present the Escalations table to the user, get answers, update the clarification block (and Edit `§clarification-log` in draft.md to record the new round), re-spawn.

State: "Feasibility: {Result} — trace {N}/{Total} satisfied, scenarios {M}/{Total} passed."

## Phase D: Materialize, Review, Finalize

### Step 10: Materialize plan.md + User Checkpoint

draft.md is complete and feasibility passed. Now distill draft.md into `plan.md` and write it to disk for the user to review.

**10.1 — Apply the distillation rules.** Read draft.md fully. Compose plan.md by selecting from each draft section per the table below; **everything not listed is draft-only** (stays in draft.md, does not appear in plan.md):

| draft.md section | What goes into plan.md |
|------------------|------------------------|
| `§meta` | `§meta` — same identity (name, date), `**Status:** draft` (will flip at Step 11), `**Source:** draft.md`, `**Note:** Run /execute-fast to implement.` |
| `§self-check` | **Draft-only.** Not in plan.md. |
| `§clarification-log` | **Draft-only.** Not in plan.md. |
| `§scope` | `§scope` — verbatim. |
| `§capabilities` | `§capabilities` — verbatim. |
| `§analysis` (per capability) | `§approaches` — per capability: `Core problem` (one sentence), `**Selected:**` and `**Committed approach:**` lines. **IF the capability had a Significant decision**, ALSO include its Approach Evaluation table (the trade-offs are informative for the executor). Otherwise omit the Approach Evaluation table. Never include the Decisions classification table or the Cascade Trace — those are draft-only reasoning artifacts. |
| `§component-notes` | `§component-notes` — verbatim. |
| `§phases` | `§phases` — verbatim. |
| `§tasks` | `§tasks` — verbatim (full table with Provides/Needs/Done when). |
| `§audit` | **Draft-only.** Not in plan.md. |
| `§feasibility-full` | `§feasibility-summary` — one paragraph: `"Validated against {N} scenarios ({H} happy / {E} edge / {F} failure); {invariants_evidenced}/{total} EVIDENCED. See draft.md §feasibility-full for the full Trace, pre-registered questions, and evidence verdicts."` |
| `§risks` | `§risks` — verbatim. |
| `§direction-summary` | **Draft-only.** Filled after user approval; not in plan.md. |

**10.2 — Write plan.md** (full file Write to `$PLAN_DIR/plan.md`) following the section order: `§meta`, `§scope`, `§capabilities`, `§approaches`, `§component-notes`, `§phases`, `§tasks`, `§feasibility-summary`, `§risks`. Each section delimited by the same `<!-- §name --> … <!-- /§name -->` tag pairs (the executor uses these as section anchors).

**10.3 — Present to the user:**

> "Plan materialized at `$PLAN_DIR/plan.md` ({N} phases, {T} tasks). Open it and review.
>
> Full reasoning, decision classifications, composition audit, and the pre-registered feasibility questions + verdicts are in `$PLAN_DIR/draft.md` if you want to see why the plan is shaped this way.
>
> Approve to finalize, or tell me what to change."

**10.4 — Handle the response.**

- **Approval** → proceed to Step 11.
- **Change request** → identify the affected draft.md section(s), apply the tagged-block Edit(s) on draft.md (never on plan.md), then re-run Step 10.1–10.3. plan.md is regenerated from draft.md each iteration. The "re-enter only the affected step" rule:
  - Disagreement with a capability → Step 3 (re-confirm), then ripple through draft sections
  - Disagreement with an approach → Step 7 for that capability only (Edit `§analysis`)
  - Structural change (phases/tasks/grouping) → Step 8 (Edit `§phases`/`§tasks`, re-audit `§audit`)
  - Reject an ACCEPTED RISK or want a `MISSING`/`WEAK` scenario invariant handled differently → Edit the relevant draft.md block (`§tasks` etc.) and re-spawn the feasibility subagent (Step 9), which rewrites `§feasibility-full`

  After any draft.md edit, re-materialize plan.md (Step 10.1–10.2) and re-present.

Re-present until approved.

### Step 11: Finalize & Freeze

The user approved the plan.md from Step 10. Now lock it.

1. **Self-verify cross-section coherence** on the just-approved plan.md. Read plan.md end to end and check:
   - Every confirmed capability is delivered by ≥1 task in `§tasks`.
   - Every `§phases` group ordering is consistent (producer phase's group strictly earlier than every consumer's).
   - **Interface integrity:** every `Needs Ph<X> contract-NN` resolves to exactly one task whose `Provides` declares that `contract-NN` in Phase X; every `Provides` is referenced by at least one `Needs` (no unconsumed contracts).
   - `§risks` reflects the scenario walkthrough outcomes (any ACCEPTED RISKs and any unresolved WEAK/MISSING notes referenced in §feasibility-summary).

   If any inconsistency is found, fix it via Step 10's flow (edit draft.md → re-materialize plan.md → re-present), not by editing plan.md directly.

2. **Flip plan.md status:** Edit only the `Status:` line in plan.md's `§meta` block: `draft` → `approved`. This is the single permitted Edit on plan.md (everywhere else it is whole-file Write at Step 10).

3. **Edit draft.md §direction-summary** to record what the user approved: today's date, the confirmed capability list (or "as in §capabilities"), the feasibility result, and any explicitly-accepted risks.

4. **Freeze draft.md.** Edit draft.md's `§meta` block: append the line `**Status:** FROZEN at approval — {YYYY-MM-DD}`. From this point, draft.md is the historical audit trail and must not be edited. If the plan is later revised, the convention is to either copy `$PLAN_DIR` to a new dated suffix or to add a new round section in draft.md — that decision is out of scope for this skill.

5. **Tell the user:**

   > "Plan approved at `$PLAN_DIR/plan.md`. draft.md is preserved as the audit trail (frozen). Run `/execute-fast` to implement — it tracks progress and realized interfaces in `$PLAN_DIR/progress.md` without modifying either of these files."

## Questions This Skill Answers

- "/plan-fast [requirement]"
- "Plan this fast but show me the capabilities first"
- "Quick plan with real capability analysis, no JSON"
- "Fast plan from gh:123 / gl:456 / jira:PROJ-789"
- "I want decomposition rigor without the full review pipeline"
