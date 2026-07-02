---
description: |
  Speed-optimized planning skill that keeps decomposition rigor but strips the
  heavy machinery. Produces a single human-readable markdown plan through
  requirement clarification, EARLY capability confirmation, parallel codebase
  discovery, per-capability approach analysis, phase/task drafting with a
  composition audit, and a coverage self-check — then one user checkpoint.
  Grounding is done UPFRONT during discovery — every integration point is verified
  LIVE against the real code as it is discovered — so there is no separate late
  grounding-verification subagent. No JSON schemas, no acceptance/test specs, no
  analysis-doc reads, no multi-dimension plan review.

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

You are producing a focused, human-readable execution plan as a single markdown file. The plan keeps the reasoning that prevents directional mistakes — requirement clarification, capability decomposition, per-capability approach selection, a cross-phase composition audit, and grounding every integration point against the real code DURING discovery (verified live, not guessed) — while dropping JSON materialization, acceptance/test specs, and the 13-dimension review. Speed comes from confirming capabilities with the user EARLY (before deep design), parallelizing codebase discovery, grounding integration points (instead of guessing them) so executors don't hit crashes, and a single user checkpoint.

**Input:** `/plan-fast "text"`, `/plan-fast ./path/to/file.md`, `/plan-fast gh:123`, `/plan-fast gl:456`, `/plan-fast jira:PROJ-789`
**Output:** `.workflow/plans/{YYMMDD}-{slug}/plan.md` — a markdown plan. It is NOT consumed by the execution skill; it is for human reading, manual execution, or discussion.

## Anti-Pattern Watchlist

### Ungrounded concrete assertion (the #1 feasibility killer)
- **Detection:** Naming a *specific* integration point as fact without having read it in the real codebase — a permission/role constant, an existing symbol or handler to hook into, the host where a long-lived process attaches, an existing file path, a response field, an existing endpoint. Symptoms: inventing a constant that exists nowhere; asserting a handler runs in a module/entry point you never opened; citing a path that doesn't exist.
- **Resolution:** Every concrete that touches *existing* code must be one of three things, never a guess:
  1. **Grounded** — you read it; cite `path:line` in `§component-notes` and reuse the *real* symbol/path/value.
  2. **Reused analog** — the exact name isn't confirmed but a real sibling exists; reuse it rather than minting a new one, and note the assumption.
  3. **Deferred** — genuinely unknown AND non-core; the task says "locate the exact insertion point (see `§component-notes`)". Deferral is for specifics the executor resolves in seconds without re-deriving design (an exact line, a field's precise name/shape) — NOT for a core decision (see the next anti-pattern).
- A wrong *invented* concrete scores worse than an honest deferral — but **a deferred core decision scores worse than a grounded committed one.** When unsure: reuse a real analog and commit with a stated assumption. Invent nothing; defer only non-core specifics.

### Over-deferral of a core decision
- **Detection:** Deferring the thing the capability hinges on — *where* the user's action is intercepted, *which* long-lived host runs the background task, *which* existing module the new flow attaches to — so the plan reads "locate the intercept point" / "add a host if none exists" for a load-bearing choice. The executor cannot even START without re-doing the design you skipped. This tanks Completeness and Actionability even when Feasibility looks honest. (It is the equal-and-opposite error to "Ungrounded concrete assertion": over-correcting from confidently-wrong into timidly-deferred.)
- **Resolution:** For any **core entry point / host / intercept**, commit to the best-grounded real candidate from discovery and state the assumption — e.g., "route the change through the existing write/save handler at `<path:line>` — the established edit path; assumes the sensitive item maps to that surface, confirm with the owner." Commit + assumption + `path:line` beats deferral. The **executor-start test:** "Can the executor begin this task without making a design decision I left open?" If no, you must make it. Deferral is only legitimate for a specific the executor fills in trivially (exact line, exact field name) — never the design choice itself.

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

### Withholding grounded concretes (false anti-HOW)
- **Detection:** Abstracting a concrete you already KNOW into a vague outcome — writing "shows the status" when discovery already found the exact status field, or "follows the existing pattern" when you read the real interface, or refusing to name the real permission constant you verified. The plan reads as outcome-only and the executor must re-derive what you already discovered.
- **Resolution:** `Done when` is an observable outcome, but it MAY and SHOULD name the **grounded** concretes it creates or touches — real file paths, the real symbol/constant/route value verified in discovery, the real response fields. Concreteness is only a fault when it is *ungrounded* (a guess) or *internal HOW that discovery didn't fix* (which data structure, which loop). For a Significant decision, the `§analysis` **Committed approach** SHOULD carry a compact grounded sketch (a type/interface shape, a config/route entry, the key call) when it removes executor ambiguity — these earn their place. The bar: name what you grounded; defer what you didn't; never invent.

### Ad-hoc contract block
- **Detection:** Writing a freeform "Shared contract", "Interface agreement", or similar prose paragraph anywhere in `plan.md` to describe a cross-phase dependency, instead of using the `Provides`/`Needs` task columns.
- **Resolution:** The two columns are the single authoritative cross-phase interface record. Put the producer semantic in `Provides` and the reference in the consumer's `Needs`. A prose block duplicates the fact in a place the executor does not read — delete it and use the columns.

## Plan File Structure & Editing Discipline

`plan.md` is a clean human-readable markdown document whose sections are delimited by **HTML-comment tags**. HTML comments render invisibly, so the document stays readable, while the tag pairs are permanent, uniquely-addressable anchors.

**The skeleton is written once** (Step 4) with every tag pair present and bodies empty except the ones filled by then. **Every subsequent write or revision is a tagged-block Edit:**

> Read `plan.md` → Edit, replacing the entire `<!-- §name -->` … `<!-- /§name -->` block (delimiters included) with the rebuilt block. Change exactly one block per Edit. Never use the Write tool on `plan.md` after the skeleton exists.

This is deterministic because the tag pair never disappears (unlike a consumed placeholder) and the delimiter names make each block a unique `old_string`; sections you do not touch are preserved byte-for-byte.

The skeleton itself is defined in [`plan-skeleton.md`](./plan-skeleton.md) — kept out of this file so the structure can be revised without churning the skill instructions. Step 4 reads that file and writes it verbatim to `$PLAN_DIR/plan.md`; subsequent steps then fill or revise the bodies between the `<!-- §… -->` tags via tagged-block Edits.

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
- **Write the full tagged skeleton to `$PLAN_DIR/plan.md` — once.** Read `.claude/skills/plan-fast/plan-skeleton.md` and Write its content verbatim to the new file (Write tool). Then Edit the three tagged blocks that are known at this point: `§meta` (name, today's date, `Status: draft`), `§scope` (in/out from Steps 2–3), and `§capabilities` (the confirmed list). Leave every other tagged body as its placeholder text. This is the only Write to `plan.md`; from here on, every change is a Read → tagged-block Edit.

State: "Wrote tagged skeleton with Scope + {N} confirmed capabilities to $PLAN_DIR/plan.md."

## Phase B: Parallel Discovery

### Step 5: Frame Discovery Subjects

Using the confirmed capabilities + `.workflow/project-overview.md` as the map, list 1–3 **discovery subjects**. Each subject is a single self-contained question whose answer shapes the plan — e.g., "How is the orders API module structured, and what pattern do existing export-style endpoints follow?" or "Where does request validation run for write endpoints, and how is it registered?"

Aim for the fewest subjects that cover the uncertain surface area. One subject is fine for an isolated change.

**Integration-point checklist (mandatory).** Before writing the subjects, enumerate every place the plan will touch *existing* code — these are the concretes that, if guessed wrong, become feasibility bugs. **This is where grounding happens — get every integration point RIGHT here, upfront, so the plan is feasible from the first draft. There is no late verification pass; discovery IS the grounding.** Typical ones:
- **Liveness — reject dead code (apply to EVERY point below).** A candidate that *exists* is not enough: confirm it is actually LIVE — reachable / called / rendered / mounted / route-registered — by grepping for its real callers/usages. A symbol with **zero callers, unmounted, or on no active route is DEAD CODE**; never build a mount, hook, gate, or intercept on it — that is the #1 silent feasibility disaster (e.g., choosing a component that turns out to have no callers). Between similar candidates, pick the one with a **verified real caller on the active path**.
- **Host / attachment point** — which existing long-lived component/module/service a hook, listener, subscription, or background task attaches to (do NOT assume a particular entry point — verify where existing long-lived concerns actually attach). **Check lifecycle viability:** the host must persist for the feature's required lifetime AND sit inside the runtime contexts the code needs (the DI container / store / provider / session scope). Work that must outlive a single screen or run across the session (a background poller, a global listener, a subscription) attaches to a **long-lived host — the app shell / root layout / service layer** — NOT a short-lived view that is torn down when the user navigates away (that silently kills it). Resolve: "what is the long-lived host inside the required context, and does it survive the flow this feature needs?"
- **Permission / access guard** — which *existing* permission/role/action constant guards the new entry point. Reuse a real one where a fitting one exists; a genuinely new surface may need a new constant — if so, follow the real naming convention you found and flag it as backend-dependent (don't silently assert it as existing).
- **Injection / trigger point** — the existing handler/callback the new behavior hooks into (e.g., the post-save success callback). Note any lifecycle interaction (does that handler also tear down or redirect, ending the context?).
- **Existing interface touched** — a response type, endpoint, parameter, or shared-state shape the plan reads or extends.

Each integration point becomes a thing a discovery subject must resolve. **A core integration point (one the capability hinges on) must end up COMMITTED to a real grounded candidate — not deferred** (see "Over-deferral of a core decision"). Fold them into the subjects so the Explore agents return the *real* symbol + `path:line` + a note on lifecycle fit for each.

### Step 6: Spawn Explore Agents in Parallel

Spawn one `Explore` subagent per subject — **all in a single message (multiple Agent tool calls)** so they run concurrently. Each prompt:
- States exactly one discovery subject
- Asks for conclusions and the specific constraints / patterns / integration points found (file path + line where it matters), not file dumps
- **Explicitly asks the agent to resolve each integration point from the Step-5 checklist that falls in its subject — return the REAL symbol/path/value and `path:line`, AND proof it is LIVE: a real caller / usage / mount / route-registration at `path:line`. If a candidate has no callers/usages it is DEAD CODE — the agent must say so and NOT propose it as a mount/hook/gate point. Report "not found" if a point genuinely doesn't exist.** (e.g., "Where do existing long-lived listeners/tasks attach, and what proves that host is live (mounted, on an active route)? What is the real permission constant for this area? What is the existing post-save success handler, and what calls it?")
- Specifies the search breadth ("medium" for a focused subject, "very thorough" if the subject spans multiple modules)

Collect the returned findings. Read `plan.md` and Edit the `§component-notes` block — one bullet per concrete constraint or pattern that shapes a phase, task, or approach (cite `path:line`). **Every integration point from the Step-5 checklist gets a resolution line. A CORE integration point (one a capability hinges on) must be `COMMITTED` — the real chosen candidate + `path:line` + a **liveness citation (the real caller/mount/route at `path:line` proving it is not dead code)** + a one-line lifecycle/assumption note (e.g., "attach to the long-lived shell — outlives the page, inside the required context"). Only a non-core specific may be `DEFERRED — executor locates exact <line/field> via <search>`. If discovery couldn't confirm a core point, commit to the best-grounded candidate and mark it an assumption — do NOT defer the design choice. No integration point is left as an unstated assumption.**

State: "Discovery complete ({N} subjects) — {M} component notes written, {K} integration points resolved ({D} deferred)."

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
- Files are concrete paths from Step 6 discovery; mark non-existent paths `[new]`. A file that touches an *existing* integration point must use the **resolved** path/symbol from `§component-notes` — or, if that integration point was `DEFERRED`, the `Done when` says "locate per §component-notes" rather than naming a guessed location.
- **`Done when` is ONE sentence describing an observable outcome** — a function/file/endpoint/UI element/behavior that exists after the task and did not before. State the user- or system-visible result. It SHOULD name the **grounded** concretes it creates or touches (real file paths, the real permission/route/symbol verified in discovery, the real response fields) — that concreteness is drop-in value, not over-specification. Do NOT prescribe internal HOW that discovery didn't fix (which data structure, which loop), and do NOT name any symbol/permission/mount you did not ground (reuse-or-defer instead — see the "Ungrounded concrete assertion" anti-pattern).
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

### Step 9: Coverage Self-Check (main session)

> **Grounding already happened — upfront, in discovery (Steps 5–6).** Every integration point was grounded
> AND verified LIVE against the real code as it was discovered, so the plan is feasible by construction — there
> is no separate late `src/`-verification subagent to run. This step is only a cheap coverage self-check.

**9.1 — Pre-flight.** Read `plan.md`. Confirm `§scope`, `§capabilities`, `§analysis`, `§phases`, `§tasks`, `§audit`, `§component-notes` have real content (not skeleton placeholder text). If not, return to the owning step.

**9.2 — Coverage check (yourself, in the main session).** Map each in-scope requirement to the delivering task(s). For any requirement with no delivering task, Edit `§tasks` to add the missing task.

**9.3 — Record.** Edit the `§feasibility` block with the Coverage Check table only (requirement → delivering tasks, one row each). Fold any accepted gaps or known-unknowns into `§risks`.

State: "Coverage {N}/{Total} requirements (grounding done upfront in discovery)."

## Phase D: Checkpoint & Finalize

### Step 10: Direction Summary & User Checkpoint

The user understands intent better than any agent — this single checkpoint is the only human review this skill has. Present, in one message:

- Plan name + scope
- The confirmed capability list
- Per-capability **Selected/Committed** lines (significant decisions as a small table: Decision | Options | Selected | Rationale)
- Phase/group overview with dependencies
- **Main flow diagram** — a runtime arrow flow (not build order) showing how the assembled pieces connect, each step labelled with the phase that produces it. Example: `User Action → API Endpoint (Ph2) → Permission Check (Ph2) → CSV Serializer (Ph1) → Stream Response (Ph2)`. A transition no phase covers is a visible gap.
- Top risks

Ask: "Approve to finalize, or tell me what to change."

On change requests, re-enter only the affected step (apply changes via tagged-block Edit):
- Disagreement with a capability → Step 3 (re-confirm), then ripple forward
- Disagreement with an approach → Step 7 for that capability only
- Structural change (phases/tasks/grouping) → Step 8 (regroup / redraft / re-audit)
- Reject an accepted deferral/risk → Edit the relevant `plan.md` block and re-run the coverage self-check (Step 9)

Re-present until approved.

### Step 11: Finalize

The assembled `plan.md` now contains every piece of context — capabilities, approaches, phases, tasks, audit, feasibility. Use it as the single source of truth for the final consistency pass.

1. **Read the full `plan.md`** end to end. Self-verify cross-section coherence:
   - Every confirmed capability is delivered by ≥1 task in `§tasks`
   - Every `§phases` group ordering is consistent with the `§audit` Group Ordering rows
   - The Coverage Check in `§feasibility` matches the current `§tasks` (no row references a task that was later edited away)
   - **Interface integrity:** every `Needs` cell `Ph<X> contract-NN` resolves to exactly one task whose `Provides` declares that `contract-NN` in Phase X, and that producing phase's execution group is strictly earlier than the consumer's; every `Provides` is referenced by at least one `Needs` (an unconsumed contract is over-declaration — clear it to `—`)
   - `§risks` reflects the scenario walkthrough outcomes (any ACCEPTED RISKs and any unresolved WEAK/MISSING notes)
   If any inconsistency is found, fix it with a single tagged-block Edit and re-Read to confirm.
2. Edit the `§meta` block: change `**Status:** draft` → `**Status:** approved`.
3. Tell the user: "Plan approved at `$PLAN_DIR/plan.md`. Run the fast execution skill (`/execute-fast`) to implement it — it tracks progress and realized interfaces in `$PLAN_DIR/progress.md` without modifying this plan."

## Questions This Skill Answers

- "/plan-fast [requirement]"
- "Plan this fast but show me the capabilities first"
- "Quick plan with real capability analysis, no JSON"
- "Fast plan from gh:123 / gl:456 / jira:PROJ-789"
- "I want decomposition rigor without the full review pipeline"
