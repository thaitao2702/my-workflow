---
description: |
  Create phased execution plans with dependency graphs, component intelligence,
  and quality review. Transforms requirements (text, files, GitHub issues, Jira
  tickets) into structured plan.json + phase files that executor agents implement.
  Use when the user wants to plan work, break down a feature, create tasks, scope
  a project, or says "let's plan this" — even if they don't say "/plan." Also
  triggers for re-planning after scope changes and multi-phase project breakdown.
  Do NOT use for direct implementation (use /execute), code review, or single-file
  changes that need no phased approach.
---

# /plan — Create Execution Plan

You are creating a detailed, dependency-aware, quality-checked execution plan. Transform requirements into phased tasks that an executor agent can implement.

**Input:** `/plan "requirement text"`, `/plan ./path/to/requirements.md`, `/plan gh:123`, or `/plan jira:PROJ-456`
**Output:** `.workflow/plans/{YYMMDD}-{name}/` directory with `plan.json`, phase JSON files, and `state.json`
**CLI reference:** `.claude/scripts/workflow_cli.reference.md` — use for all plan/phase/state operations. Read it to find exact command syntax.

## Expert Vocabulary Payload

**Requirements Analysis:** requirement elicitation, clarification round (max 3), implicit requirement discovery, scope boundary (in_scope/out_of_scope), unhappy path analysis, ambiguity resolution

**Plan Architecture:** phased execution plan, dependency graph (DAG), parallel execution group, task granularity (coherent unit), phase sizing (one-agent-session), mission briefing (plan summary), acceptance criteria (verifiable-by-running)

**Problem Decomposition:** capability decomposition (MECE), decision classification (constrained/conventional/significant), decide-then-descend, cascade check, approach evaluation, commitment point, combinatorial pruning

**Component Intelligence:** analysis doc freshness (fresh/stale/missing), progressive loading level (0/1/2), component role classification (Modified/Extended/Consumed/Created), analysis gate, knowledge layer

**Quality Assurance:** plan review (13-dimension evaluation), direction checkpoint (Step 6), revision round (max 2), automated review before user review

**Knowledge Capture:** corrections log, findings log, documentation contradiction, doc status (contradicts_analysis/missing_from_analysis/contradicts_overview/missing_from_overview), post-planning knowledge update

## Anti-Pattern Watchlist

### Parallel File Conflict
- **Detection:** Phases in the same execution group modify the same files. Causes merge conflicts when phases run in parallel.
- **Resolution:** Check every file in `tasks[].files` across phases in the same group. If any file appears in two phases within the same group, move one phase to a later group.

### Analysis Over-Read
- **Detection:** Invoking `/analyze` during planning. Reading 20+ source files when 5 would suffice. Extensive codebase exploration without producing plan content.
- **Resolution:** Use analysis docs when fresh, read source directly when stale/missing. Defer `/analyze` to the execution analysis gate (Step 2a in `/execute`). Explore enough to plan, then start designing.

### Skipped Direction Checkpoint
- **Detection:** Full plan JSON written without presenting a direction summary to the user first. User sees the complete plan as the first output.
- **Resolution:** Always complete the full decomposition (Steps 5a-5d) and get user approval (Step 6) before writing plan files (Step 7). Catching directional mistakes early is cheap; rewriting a reviewed plan is expensive.

### Undefined Cross-Phase Interface
- **Detection:** Phase X's task says "calls the bridge helper" or "receives helpers via injection" but neither Phase X nor the defining phase declares the dependency in `interface_contracts`. Two independent executor agents will have no coordination, and the consuming agent won't receive the producing agent's interface.
- **Resolution:** Identify every cross-phase code dependency — any place where Phase X's code imports or calls Phase Y's code. For each: (1) Add an `interface_contracts` entry on the defining phase (the provider) with contract ID, expected class name, purpose, and consumed_by_phases. (2) Ensure the producing phase is in an earlier execution group than all consuming phases (sequential enforcement). (3) In the consuming phase's task description, reference the contract: "Receives BridgeHelper (Phase 3 contract-01)." Private and internal functions within a single phase do not need declarations — they are the executor's domain.

### False Options
- **Detection:** Generated alternatives differ in ways that don't change any phase, task, or dependency in the plan. The choice may be real but belongs at implementation time, not planning time. Example: "Express vs Fastify" for a simple CRUD API where both produce identical plan structure.
- **Resolution:** Before treating a choice as a planning-level decision, trace the cascade — does switching between options change the phase structure, add/remove tasks, or alter dependencies? If no → note as an implementation recommendation in the task description, not a planning decision. If yes (e.g., Express → Node → single-threaded → need worker threads for CPU-intensive export → new task/phase) → it IS a planning-level decision requiring approach evaluation.

### Premature Branching
- **Detection:** Generating approach options for decisions that are already constrained (project uses X) or conventional (obvious best practice). Wastes tokens and creates false rigor.
- **Resolution:** Apply the decision classification filter before generating options. If the project already uses a framework, if the codebase already has an established pattern, or if only one viable approach exists — classify as constrained or conventional and move on. Only generate alternatives for significant decisions.

### Uncommitted Descent
- **Detection:** Proceeding to phase composition or the next capability while carrying multiple open approaches from a previous decision. Causes combinatorial explosion — 3 open decisions × 3 options = 27 implicit plan variants the agent tries to hold in working memory.
- **Resolution:** Each significant decision must end with "**Selected:** [approach] — [rationale]" before proceeding to the next capability or to phase composition. The next step operates within committed selections only.

## Phase A: Requirement Gathering

### Step 1: Parse Input

Determine the input source and extract requirements:

| Input Pattern | Action |
|--------------|--------|
| `"quoted text"` or plain text | Use directly as requirements |
| `./path/to/file.md` | Read the file, extract requirements |
| `gh:123` or GitHub URL | Use the Skill tool to invoke `/github` with the issue reference |
| `gl:123` or GitLab URL | Use the Skill tool to invoke `/gitlab` with the issue reference |
| `jira:PROJ-456` | Use the Skill tool to invoke `/jira` with the ticket ID |

### Step 2: Template Discovery

Before planning, check if an existing template matches these requirements:

1. Read `.workflow/templates/index.md`
2. Match requirements text against template `Trigger Keywords`
3. Based on match count:
   - **0 matches** → no template applies. Proceed to Step 3.
   - **1 match** → too weak a signal (e.g., "table" could match anything). Skip template. Proceed to Step 3.
   - **2+ matches** → likely relevant. Tell the user: "Found matching template: **{name}** — {description}"
     - Ask: "Use this template as a starting point? (yes/no/show me)"
     - If yes: use the Skill tool to invoke `/template-apply` with the template name. Use its output as the basis for planning.
     - If "show me": display the template overview, then ask again
     - If no: proceed with normal planning

### Step 3: Clarification

Analyze requirements for gaps and ambiguities. The structured self-check below forces depth — do not skip categories.

1. Read `.workflow/project-overview.md` for architectural context

2. **Self-check before generating questions.** Output this table — every row must be filled (use "None identified" only after genuine analysis):

   **Self-Check Findings:**
   | Gap Category | Concrete Gap Identified | Generated Question (or "None") |
   |--------------|------------------------|-------------------------------|
   | Implicit requirements (auth, validation, error handling, permissions) | [what's assumed but unstated] | [specific question] |
   | Data sources / dependencies / external systems | [what data/system is needed but unmentioned] | [specific question] |
   | Unhappy paths / edge cases | [what scenario would break this] | [specific question] |
   | Scope boundaries | [what's explicitly NOT included] | [specific question] |

3. Generate clarification questions from the table's "Generated Question" column above. Drop "None" rows. Apply this phrasing rule:
   - Specific and concrete: "Should the export feature support CSV only, or also Excel/PDF?" — good
   - Decision-forcing: "When the payment fails, should the order stay pending or be cancelled?" — good
   - NOT open-ended: "Can you tell me more about the requirements?" — bad

4. Present questions to user, wait for answers
5. Loop until no more genuine gaps (max 3 clarification rounds). On each new round, re-output the Self-Check Findings table with updated rows reflecting what the user's answers resolved and what new gaps surfaced.

6. **After clarification rounds complete**, check if the user corrected any assumptions that contradict existing documentation. If so, record them:

**Corrections Log:**
| Correction | Source | Contradicts | Target Doc |
|-----------|--------|-------------|------------|

Only record corrections where existing documentation (analysis docs, project-overview) says something different from what the user clarified. Not new requirements — contradictions of existing documented knowledge. Examples:
- User says "that service doesn't handle retries anymore" but analysis doc says it does → record
- User says "the feature should support CSV export" (new requirement) → don't record

If no corrections: write "None" under the table header.

7. **Initialize plan directory.** After clarifications and corrections are complete (or skipped if no gaps existed):

   - Derive a kebab-case `{slug}` from the consolidated requirement (e.g., "Add CSV export to orders API" → `add-csv-export-orders-api`)
   - Compute `$PLAN_DIR = .workflow/plans/{YYMMDD}-{slug}/` where `{YYMMDD}` is today's date
   - Create the directory if it doesn't exist (no files inside yet)

   Each subsequent Phase C step writes ONE artifact file into `$PLAN_DIR`:

   | Step | File written |
   |------|--------------|
   | 5a | `capabilities.md` — numbered capability list |
   | 5b | `decisions.md` — per-capability analysis blocks |
   | 5c.1 | `phase-grouping.md` — bulleted phase list with execution groups |
   | 5c.2 | `task-drafts.md` — per-phase task tables |
   | 5c.3 | `audit.md` — Phase Composition Audit table |

   Per-file artifacts let later steps update earlier ones deterministically: a small focused file can be fully rewritten (Write tool) when substantial changes are needed, or surgically Edited when small changes apply. `$PLAN_DIR` is reused throughout — Step 7 writes `plan.json` and `phase-{N}.json` alongside these files.

If every row of the Self-Check Findings table is "None identified" — requirements are clear and complete — skip steps 3-6 above (no clarification needed); still complete step 7 above before proceeding to Phase B.

## Phase B: Component Intelligence Gathering

### Step 4: Read Affected Components

From requirements + project overview + clarification answers, identify specific components that this plan will touch.

#### Step 4a: Identify Components

Browse the codebase (Glob, Grep) to find the specific files and modules involved. Classify each component's role in this plan:

| Role | Meaning |
|------|---------|
| **Modified** | Changing its internals |
| **Extended** | Adding new features to it |
| **Consumed** | Calling its API from new code |
| **Created** | New component, checking similar existing ones |


#### Step 4b: Read Component Knowledge (analysis-first)

For each affected component, use the analysis doc as the primary source when it's verified fresh. This saves significant tokens compared to reading full source, and analysis docs contain accumulated experience (hidden behaviors, edge cases, failed assumptions) that source code alone doesn't capture.

**For each component:**

1. **Check freshness:** Use the CLI `analysis check` command for each affected component.

2. **Act on result:**
   - **`fresh`** → use the CLI `analysis read --level 1` command to read the analysis doc. Judge whether this gives you enough to plan — if yes, skip source. If you need more detail (e.g., exact internal flow for a complex modification), read source selectively.
   - **`stale`** → skip the analysis doc — read source directly instead.
   - **`missing`** → read source directly.

3. **What to read from source** (when falling back):
   - Modified/Extended components: read thoroughly — every function, not just exports
   - Consumed components: focus on public API / exports
   - Created components: read source of similar existing components for reference patterns

4. **Capture component findings.** This is the source for `component_intelligence` in Step 7.

   Finding Type values:
   - `constraint` — limit imposed by the component (size, rate, format, type)
   - `hidden behavior` — non-obvious runtime behavior not visible from the signature
   - `integration point` — how this component connects to others (events, callbacks, shared state)
   - `pattern to follow` — established convention in similar existing components

   Rules:
   - Every component you read must produce at least one row
   - Use "No plan-shaping findings — straightforward usage" only after genuine analysis (not as a default)
   - "How It Shapes the Plan" must reference a concrete plan effect (phase, task, constraint) — not vague "will affect design"

   **Now output the table:**

   **Component Intelligence Findings:**
   | Component | Finding Type | Finding | How It Shapes the Plan |
   |-----------|-------------|---------|------------------------|
   | [path] | constraint / hidden behavior / integration point / pattern to follow | [specific fact, e.g., "clamps date ranges to 90 days silently"] | [e.g., "export feature needs pagination — affects Phase 2 design"] |

5. **Log documentation contradictions.** If you discover anything that contradicts or is missing from existing documentation, log it:

**Findings Log:**
| Component | Finding | Doc Status | Target |
|-----------|---------|-----------|--------|

Doc Status values:
- `contradicts_analysis` — analysis doc states X, but source shows Y
- `missing_from_analysis` — source has non-obvious behavior not captured in analysis doc
- `contradicts_overview` — project-overview describes something inaccurately
- `missing_from_overview` — project-overview is missing relevant architectural context

Only non-obvious findings — not "the function exists" but "the analysis doc says async but the code is synchronous." If no findings: write "None" under the table header.

**Do NOT invoke `/analyze` during planning.** If an analysis doc is stale or missing, read source directly. Analysis generation is expensive (subagent overhead) and best deferred to the execution analysis gate (Step 2a in `/execute`).

**Re-anchor (before Phase C):** Before crossing into Phase C and starting Step 5, do both reads below — they place phase instructions and principles adjacent to your generation point, where attention is strongest.
1. Use the Read tool to load the Phase C section of `D:\Project\my-workflow\.claude\skills\plan\SKILL.md` from "## Phase C: Plan Creation" through the end of Step 7, load the instruction, not just the heading.
2. Read `.claude/skills/plan/planning-reference.md` — it contains the planning principles, decision classification guide, and generation constraints that govern Steps 5-7. Apply them throughout Phase C.

## Phase C: Plan Creation (Main Agent)

You design the plan directly — no subagent delegation. All context from Phases A-B is already in your session.

### Step 5: Problem Decomposition & Approach Design

Design the plan through layered reasoning — decompose first, then analyze each piece, then compose into phases. Process one layer at a time; commit decisions before descending to the next layer.

#### Step 5a: Capability Decomposition

From requirements + clarification answers + component intelligence, identify the distinct capabilities this plan needs to deliver. Each capability is an independent functional unit that delivers user-visible or system-visible value.

Rules:
- Aim for MECE (mutually exclusive, collectively exhaustive) — no overlaps, no gaps
- Each capability should be describable in one sentence
- If a requirement maps to a single obvious capability, that's fine — not everything needs decomposition
- If you identify more than 7 capabilities, group related ones into domains first

**Complexity gate:** If there is only 1-2 capabilities with obvious approaches (no significant architectural decisions), collapse Steps 5b-5c into a brief note: "Approach: [description], follows existing [convention/pattern]" — then skip directly to Step 5d.

**Now write `$PLAN_DIR/capabilities.md`** using the Write tool. File content:

```
# Capabilities

1. [Capability name] — [what it does, one line]
2. [Capability name] — [what it does, one line]
3. ...
```

After the Write completes, briefly state in the conversation: "Wrote {N} capabilities to capabilities.md."

#### Step 5b: Per-Capability Analysis & Approach Selection

Process capabilities **one at a time**. Output the full analysis for each capability before moving to the next. This forces step-by-step reasoning and prevents combinatorial explosion.

Rules:
- **Decide-then-descend:** the "Selected" and "Committed approach" lines are mandatory before moving to the next capability. No open options carried forward.
- **Classify before branching:** apply the decision classification filter (see `planning-reference.md`) to every decision. Only significant decisions get approach evaluation.
- **Cascade check:** before classifying a decision as constrained/conventional, trace its implications — does the choice cascade into phase-level changes? If yes, it's significant regardless of how "obvious" it seems. The Cascade Trace cell in the Decisions table must be filled for EVERY decision, not only Significant ones.
- **Max 3 approaches** per significant decision. If you see more, you're decomposing at the wrong level.
- Later capabilities can reference earlier committed decisions: "Given Cap 1's selection of [X], this constrains the approach to..."

**Now write `$PLAN_DIR/decisions.md`** using the Write tool. Process capabilities one at a time — derive each block, then write the file once with all blocks (the file is small enough that a single Write is simpler than multiple Edits).

File structure:

```
# Per-Capability Analysis & Approach Selection

### Capability 1: [Name]
{block — see format below}

### Capability 2: [Name]
{block — see format below}
```

Block format (per capability):

```
### Capability N: [Name]

**Core problem:** [What's the actual technical challenge? 1-2 sentences]

**Decisions:**
| Decision | Classification | Cascade Trace | Rationale |
|----------|---------------|---------------|-----------|
| [what needs deciding] | Constrained / Conventional / Significant | [implications traced — does this choice change phase structure, add tasks, or alter dependencies? "None — purely local" is valid only after explicit trace] | [why this classification — constraint source / convention / why the cascade makes it significant] |

[IF significant decisions exist:]

**Approach evaluation: [decision name]**
| Approach | What | Key Trade-off | Fit |
|----------|------|---------------|-----|
| [name] | [1-line description] | [main pro vs con] | [fit with project context] |
| [name] | [1-line description] | [main pro vs con] | [fit with project context] |

**Selected:** [approach] — [1-line rationale]

**Committed approach:** [1-line summary of how this capability will be built]
```

After the Write completes, briefly state in the conversation: "Wrote analysis for {N} capabilities to decisions.md."

#### Step 5c: Phase Composition

All capabilities have committed approaches. Compose them into phases, draft the tasks within each phase, then audit the composition. Each sub-step's output feeds the next.

1. **Group capabilities into phases** — by cohesion, dependency order, and parallel safety. A single capability may span multiple phases if it has natural sequential stages. Assign each phase to an execution group (A, B, C…). Phases in the same group run in parallel and MUST NOT modify the same files.

   **Now write `$PLAN_DIR/phase-grouping.md`** using the Write tool. File content:

   ```
   # Phase Grouping

   - **Phase 1: [Name]** (Execution Group A) — Capabilities: [1, 3]
   - **Phase 2: [Name]** (Execution Group B) — Capabilities: [2]
   - ...
   ```

   After the Write, briefly state in the conversation: "Wrote {N} phases (groups: A=..., B=..., ...) to phase-grouping.md."

2. **Draft the task list per phase.** Without committed tasks, the audit below would reference tasks that exist only in your mind — non-deterministic and unverifiable. Commit task identity, files, and the **outcome** here so the audit cites real entries; Step 7 enriches each task with acceptance_criteria and test_requirements.

   **Key principle: task drafts capture WHAT each task delivers, never HOW.** The `Done when` cell describes an observable outcome that did not exist before the task ran. The executor decides HOW by reading source — that is execute-time territory.

   Rules for the task drafts:
   - Each task is a coherent unit of work (one logical change, one commit's worth — see "Task Granularity" in `planning-reference.md`)
   - Task IDs are `task-01`, `task-02`, ... within each phase (numbering resets per phase)
   - Task name is short and action-oriented (e.g., "Create CSV serializer module")
   - Files list is concrete — paths discovered in Step 4b reads. If a path doesn't yet exist, mark it `[new]` after the path.
   - **`Done when` is ONE sentence describing the outcome** — a function/file/UI element/behavior that exists after this task that did not exist before. State the user-visible or system-visible result. Do NOT describe the steps to get there.
   - **The executor-source test:** Read your `Done when` cell as if you are the executor. Ask "Will I need to read source code to figure out HOW?" If the answer is no, you over-specified — rewrite to describe an outcome, not a recipe.

   GOOD vs BAD `Done when` examples:

   | Task name | BAD (implementation, HOW) | GOOD (outcome, WHAT) |
   |-----------|---------------------------|---------------------|
   | Add agent-listing query endpoint | "Inject builder.query at URL `agentgamecurrency/list-by-game`, body `{gameId, currencyIds, page, pageSize, search?}`, no tags, keepUnusedDataFor: 0, add transformResponse mapping `{currencyId, currencyCode}` to `{id, code}`, export `useGetAgentsByCurrenciesQuery`." | "AgentApi exports a hook that returns paginated agents filtered by the currencies the form has selected, in the shape the existing currency-list component consumes." |
   | Wire Agent Assignment tab into GameUpdate | "Insert items[] entry at index 3 using `loadable(() => import('./components/FormAgentAssignment'))`; pass `form`, `gameId={Number(id)}`, `onInitedFormFieldDone`, and a `ref`." | "GameUpdate renders an Agent Assignment tab between Paytable and Review&Submit; the form receives the same refs and props as the existing tabs." |

   **Now write `$PLAN_DIR/task-drafts.md`** using the Write tool. File content — one `### Phase N: [Name]` block per phase, each containing a task-draft table:

   ```
   # Task Drafts

   ### Phase 1: [Phase Name] (Execution Group [A])

   | Task ID | Name | Capability | Files | Done when (outcome, WHAT not HOW) |
   |---------|------|-----------|-------|-----------------------------------|
   | task-01 | [name] | [Cap N] | `path/one.ts`, `path/two.ts [new]` | [observable outcome in one sentence] |
   | task-02 | ... | ... | ... | ... |

   ### Phase 2: [Phase Name] (Execution Group [B])

   | Task ID | Name | Capability | Files | Done when (outcome, WHAT not HOW) |
   ...
   ```

   After the Write, briefly state in the conversation: "Wrote task drafts for {N} phases ({M} tasks total) to task-drafts.md."

   When Step 5c.3 audit triggers remediation (new wiring task, etc.), this file is the target of those Edits — section headers (`### Phase N: [Name] (Execution Group [X])`) are stable anchors within the file.

3. **Audit the composition.** With phase boundaries committed in 5c.1 and tasks committed in 5c.2, surface cross-phase concerns. Identifying integration tasks happens here — Transition rows reveal what wiring tasks must exist (which then go into the 5c.2 tables).

   Concern Type definitions:
   - **Transition** — a runtime control or data flow between phases. Every user-action → system-response path must be fully covered by Transition rows. A missing Transition = a gap in the plan.
   - **External Consumer** — a task modifies an existing interface (function signature, return type, props, API contract, DB schema, config shape, event payload, etc.) and the change could break code outside the plan.
   - **Group Ordering** — verifies the producer's execution group is strictly earlier than the consumer's, with no circular dependencies.

   Rules for filling this table:
   - **References must be real:** all task and phase references in the Producer/Consumer columns MUST match real entries in `$PLAN_DIR/task-drafts.md`. If you need a task that doesn't exist there, Edit `task-drafts.md` to add it FIRST, then come back here.
   - **Transition coverage:** every cross-phase relationship in the runtime flow gets a row. Trace end-to-end from user action to system response — if no Transition row covers a step in that flow, the plan has a gap.
   - **External Consumer coverage:** every plan task that modifies an existing interface gets a row. Grep for consumers of the **specific** interface being changed — not the entire component. "Backward compatible" requires a concrete reason (e.g., "new optional parameter", "additive enum value"), not just an assertion.
   - **Group Ordering coverage:** every cross-phase code dependency (Phase X imports, calls, or receives objects created by Phase Y) gets a Group Ordering row. Assign a provisional `interface_contracts` ID (`contract-01`, `contract-02`, …) scoped to the defining phase — Step 7 materializes these as JSON entries using the IDs assigned here. Every Transition row whose producer and consumer phases differ also gets a corresponding Group Ordering row.

   **Remediation rule.** For every audit row whose concern requires a plan change, take the change against the relevant artifact file BEFORE moving to the next row:

   - **Transition GAP** → Edit `$PLAN_DIR/task-drafts.md` to add a new task row to the appropriate phase's table (anchor on the `### Phase N: ...` header).
   - **External Consumer requiring update** → Edit `$PLAN_DIR/task-drafts.md` to add a task row to whichever phase owns the consumer surface.
   - **Group Ordering violation (MOVE)** → Edit `$PLAN_DIR/phase-grouping.md` to relocate the phase to a later group, AND edit the corresponding `### Phase N: ...` header in `$PLAN_DIR/task-drafts.md` to update its "(Execution Group X)" label.
   - **Circular dependency** → Edit `$PLAN_DIR/phase-grouping.md` and `$PLAN_DIR/task-drafts.md` to either merge phases (combine the affected `### Phase N: ...` blocks) or extract the shared interface into a new earlier phase. For substantial restructures, prefer fully rewriting the affected file with the Write tool over surgical Edits.
   - **Approach revision** → Edit `$PLAN_DIR/decisions.md` to update the affected capability's `Committed approach` line.

   After applying the Edit, fill the audit row's `Notes` column with a sentence describing the change ("Added task-04 to Phase 2 — wires CSV serializer to streaming response"). Set `Status` to `OK`. Re-run any audit row affected by the Edit (e.g., adding a new task may resolve another Transition row that depended on it).

   **Escalation when stuck.** If an audit row's required change cannot be applied in one revision pass — typically because the change would violate a user-clarification constraint or would require structural redesign beyond simple task additions — do NOT loop indefinitely. Set `Status` to `ESCALATED` and present the row to the user with 3 options:

   > "Audit row #N could not be resolved:
   > - **Concern:** [Subject]
   > - **Proposed change:** [what you tried]
   > - **Blocker:** [why it can't be applied autonomously]
   >
   > Please choose:
   > 1. Apply suggested change manually — describe edit details for my confirmation
   > 2. Modify the change — specify a different approach
   > 3. Accept the gap as risk — provide rationale; I'll record it in Notes and set Status to OK"

   Apply the user's choice (perform the Edit on the relevant artifact file, or record the ACCEPTED RISK rationale in the Notes column of `audit.md`), then continue with remaining audit rows. Do not proceed to Step 5d until every audit row has `Status = OK`.

   **Now write `$PLAN_DIR/audit.md`** using the Write tool. File content begins with `# Phase Composition Audit` followed by the table below. As remediations are applied to other artifact files, update this file's `Status` and `Notes` columns by editing in place (use the Edit tool against the specific row).

   **Phase Composition Audit:**
   | # | Concern Type | Subject | Producer / Source | Consumer / Target | Status | Notes |
   |---|--------------|---------|-------------------|-------------------|--------|-------|
   | 1 | Transition | [data or control flow, e.g., "HTTP request body → handler"] | [Phase X / task-N from 5c.2] | [Phase Y / task-M from 5c.2] | OK ∣ ESCALATED | [resolution description, e.g., "Covered by task-04 in Phase 2" or "Added task-05 to Phase 2 — wires producer to consumer"] |
   | 2 | External Consumer | [modified interface + specific change, e.g., "UserService.findById return type now Promise<User \| null>"] | [plan task-N that modifies] | [external file paths from grep, OR "None — no external consumers"] | OK ∣ ESCALATED | [resolution, e.g., "Backward compatible — new optional parameter, existing callers unaffected" or "Added task-08 to Phase 3 updating src/admin/dashboard.ts"] |
   | 3 | Group Ordering | [interface_contracts ID, OR a Transition row's # from above] | [Phase X / Group A] | [Phase Y / Group B] | OK ∣ ESCALATED | [resolution, e.g., "Direction correct — Phase X (Group A) precedes Phase Y (Group B)" or "Moved Phase Y to Group C" or "Resolved circular by merging Phase X into Phase Y"] |

#### Step 5d: Feasibility Walkthrough (subagent-driven)

Before presenting to the user, validate the plan by simulating its completion. Step 5c's Phase Composition (phase grouping, task drafts, audit) committed WHAT the plan is; this step verifies WHETHER it would actually work.

**Why a subagent.** A separate-context subagent reduces author bias — you designed the plan, so your judgment of "would this work?" inherits your blind spots. The subagent reads the plan fresh and produces evidence-cited findings. You apply revisions; the subagent never edits plan files.

This catches the class of defects the structural plan-reviewer (Step 8) cannot — feasibility failures, missing capabilities at integration points, and assumptions that won't hold under real implementation.

**Sub-step 5d.1 — Verify all Phase C artifact files exist.**

`$PLAN_DIR` already exists from Step 3.7 (Phase A end). Confirm before invoking the subagent that all five artifact files exist and are non-empty:

- `$PLAN_DIR/capabilities.md` (Step 5a)
- `$PLAN_DIR/decisions.md` (Step 5b)
- `$PLAN_DIR/phase-grouping.md` (Step 5c.1)
- `$PLAN_DIR/task-drafts.md` (Step 5c.2)
- `$PLAN_DIR/audit.md` (Step 5c.3) — every row's `Status` must be `OK` (escalations resolved with user input)

If a file is missing, or the audit has any non-OK row, return to the corresponding step and complete it before proceeding.

**Sub-step 5d.2 — Spawn the feasibility-validator subagent.**

Read the prompt template: `.claude/skills/plan/feasibility-prompt.md`.

1. Collect each data item listed in **For Orchestrator — Data to Collect** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected values (paths as raw strings; the `requirements_in_scope` and `user_clarification` blocks as inline bulleted text — capture every nuance from Phase A that affects feasibility)
3. Spawn the **feasibility-validator subagent** (`.claude/agents/feasibility-validator.md`) **in foreground**, passing the filled **For Subagent** section as the prompt. Foreground gives progress visibility and avoids redundant launches if the agent appears stalled.

**Sub-step 5d.3 — Parse response and apply revisions.**

Per the template's "For Orchestrator — Expected Output" section:

- **On `PASS`:** store the trace + premortem for Step 6 presentation; proceed to Step 6.
- **On `FAIL_REVISION_NEEDED`:**
  - For each trace row with Verdict ≠ DEMONSTRABLY_SATISFIED: Edit the relevant artifact file — typically `$PLAN_DIR/task-drafts.md` (add task, change description, change files) or `$PLAN_DIR/audit.md` (add audit row + corresponding remediation in another file).
  - For each premortem Mitigation that's a plan change: apply it by Editing the appropriate file (`task-drafts.md`, `decisions.md`, `phase-grouping.md`, etc.).
  - Re-spawn the subagent (**max 2 revision rounds total**).
  - If still `FAIL_REVISION_NEEDED` after 2 rounds: present the findings to the user and ask how to proceed (`approve as-is with accepted risks` / `apply specific revisions and re-run` / `escalate to deeper rework`).
- **On `FAIL_AMBIGUOUS`:** present the Escalations table to the user immediately. Wait for clarification. Update your in-conversation `user_clarification` block with the new answers (no artifact file change unless a Phase C section is affected), and re-spawn the subagent.

**Sub-step 5d.4 — Hold the final trace + premortem.**

The trace + premortem from the final passing (or final-attempt) subagent response is the artifact you present to the user in Step 6 alongside the direction summary. Do NOT regenerate it yourself — Step 6 shows the subagent's output verbatim.

### Step 6: Direction Summary & User Checkpoint

The user understands the requirements better than any agent — catching directional mistakes here is cheap; running a 13-dimension review on a plan the user would reject is waste. This step synthesizes the direction summary AND presents it (with Step 5d's Feasibility Walkthrough) to the user in one operation.

**Sub-step 6.1 — Synthesize the direction summary.** Read the Phase C artifact files in parallel (`$PLAN_DIR/capabilities.md`, `decisions.md`, `phase-grouping.md`, `task-drafts.md`, `audit.md`) for source data. Compose the following for user review (do NOT produce full JSON yet):

- Plan name and scope
- Number of phases (from `phase-grouping.md`) and total tasks (count rows across `task-drafts.md`)
- Phase overview with dependency groups and key dependencies (from `phase-grouping.md`)
- **Main flow diagram** — show how the pieces connect at runtime (not build order). Use a simple text flow with arrows showing data/control flow through the system once all phases are assembled. Label each step with the phase that produces it. This makes composition gaps visible — if no phase covers a transition, the gap is obvious.

  Example:
  ```
  User Action → API Endpoint (Ph2) → Permission Check (Ph3) → CSV Serializer (Ph1) → Stream Response (Ph2)
  ```

- **Key decisions table** (significant decisions only):
  ```
  | Decision | Options Considered | Selected | Rationale |
  |----------|-------------------|----------|-----------|
  ```
- Top risks (informed by Step 5d's Premortem mitigations)

**Sub-step 6.2 — Present to the user.**

1. Show the direction summary from 6.1 AND the Step 5d feasibility-validator subagent's output verbatim (Requirement Satisfaction Trace + Premortem + any Escalations rows)
2. Ask: "Does this direction look right? Approve to proceed, or tell me what to change."
3. If user wants changes:
   - If the user disagrees with a key decision from the table, re-enter Step 5b for that specific capability only — don't redo the entire analysis
   - For structural changes (add/remove phases, change grouping, change tasks), revise Step 5c (regroup phases in 5c.1, revise task drafts in 5c.2, re-run audit 5c.3)
   - If the user wants to address a premortem risk differently or rejects an "ACCEPTED RISK" rationale, Edit the relevant artifact file (`$PLAN_DIR/task-drafts.md`, `$PLAN_DIR/decisions.md`, etc.) and re-spawn the feasibility-validator subagent (return to Step 5d.2-5d.3) for the affected rows
   - Re-synthesize the direction summary in 6.1 with the updates, then re-present
   - Repeat until user approves direction
4. If user approves: proceed to Step 6.5

### Step 6.5: TDD Strategy Callout (mandatory before Step 7)

Output an explicit TDD Strategy block in the planning transcript before writing any `test_requirements` field. This eliminates speculative "if a test runner is added later" phrasing at its source.

Process:
1. Check `package.json.scripts.test` (or the project's equivalent) and `.workflow/project-overview.md` § Testing
2. Output the block below; every field MUST be filled

```
**TDD Strategy:**
- **Test runner detected:** {exact name like "Vitest" / "Jest" / "Pytest"; or "None — confirmed by absence of test script in package.json AND no test framework dependencies"}
- **Policy applied:** {"TDD default — tests first" if runner present; "TDD exception per project policy" if absent, citing the path to the TDD policy doc (e.g., `.claude/rules/tdd-policy.md`)}
- **Test requirement template:** {the verbatim phrasing that will appear in `test_requirements` arrays for tasks where the exception applies — e.g., "No test runner in this project; manual verification scenario: [...]". NEVER `"if a test runner is added later"` or similar future-conditional speculation.}
```

The template phrasing becomes the canonical wording for every applicable task's `test_requirements` entry in Step 7. If the runner IS present, the template field reads "Standard TDD — write test first, then implementation" and Step 7's task entries use that pattern instead.

### Step 7: Write Plan Files

Direction approved — now materialize the full plan to disk.

**Read the Phase C artifact files first** — they are the source of truth for everything Phase C produced. Read in parallel: `$PLAN_DIR/capabilities.md`, `$PLAN_DIR/decisions.md`, `$PLAN_DIR/phase-grouping.md`, `$PLAN_DIR/task-drafts.md`, `$PLAN_DIR/audit.md`. Phase A/B clarifications and component intelligence come from conversation (they live there by design — not persisted as files).

**Read `.claude/skills/plan/plan-phase-formats.md` now.** It contains the `plan.json` and `phase-{N}.json` format specifications with all field definitions. Follow these formats for sub-steps 2-5.

**Requirement coverage sanity check.** After writing `acceptance_specs` across all phases (sub-step 4 below), scan once: for each entry in `plan.json.scope.in_scope`, identify the spec(s) that verify it. If any requirement has only structural specs (grep-based) and no behavioral spec (runtime-exercising), add a behavioral spec before invoking the reviewer in Step 8.

---

1. Use the existing `$PLAN_DIR` from Step 3.7 (Phase A end). The directory `.workflow/plans/{YYMMDD}-{slug}/` already exists with the five Phase C artifact files inside. Leave them in place as a planning audit trail — they document the full Phase C evolution including audit remediations and are small enough to keep alongside the final JSON files.

2. Write `plan.json` with `"status": "draft"` following the plan file format
3. Write `phase-{N}.json` for each phase following the phase file format
4. **Write acceptance specs:** For each phase, derive `acceptance_specs` that verify the phase delivers its requirements. Review each phase's tasks against the overall `scope.in_scope` requirements. Every requirement should trace to at least one spec across all phases. Write specs into the phase JSON files. Specs should cover functional correctness — not code quality (that's the reviewer's job).
5. **Materialize `interface_contracts` from the Step 5c.3 audit.** Do not re-identify dependencies and do not re-check ordering — the audit is authoritative on both. This step is pure materialization.

   For each Group Ordering row in the 5c.3 audit table, write an `interface_contracts` entry on the **defining phase's** JSON (the Producer phase in the row) following the format in `plan-phase-formats.md`:
   - `id` — the contract ID assigned in the audit (e.g., `contract-01`)
   - `name` — expected class or module name
   - `description` — one-line purpose
   - `file` — path where the interface will be created
   - `defined_in_task` — task-id within the defining phase that creates it
   - `consumed_by_phases` — list of consuming phase numbers (the Consumer column from the audit)
   - `interface_plan[]` — the **planner's** semantic contract. For each public function, class, action, or component consumers will use, specify: `name`, `type` (Redux action / class / React component / utility function / etc.), `purpose` (one line: what capability this delivers), `inputs_semantic` (English description of what the consumer supplies — NOT a type literal), `outputs_semantic` (English description of what the consumer can do with the result), `consumer_invariants` (behaviors and edge cases the consumer can rely on). Pre-pinning an exact TypeScript/Python type literal is permitted ONLY when re-exporting an existing project type — cite the existing type's location with `file_path:line_number` evidence in that same Pattern Claim Verification table.
   - `interface_actual[]` — write `[]` (empty array). This field is populated later by the producing executor at execute time via `state set-interface-actual` — the planner never writes it.

   In each **consuming phase's** task description, add a contract reference: "Receives BridgeHelper (Phase 3 contract-01) via constructor injection."

   The planner's `interface_plan[]` is the coordination contract — semantic, stable across implementation choices. The executor's `interface_actual[]` (filled at execute time) provides the realized signature for consuming executors. If the consumer needs deeper detail at execute time, both `interface_actual[]` and the `file` path are available. Internal functions within a single phase remain the executor's domain — they do not appear here.
6. Use the CLI to read back the plan and verify files written correctly

## Phase D: Quality Review

### Step 8: Automated Review

Read the prompt template: `.claude/skills/plan/plan-reviewer-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions and review dimensions
3. Spawn a **plan-reviewer subagent** (`.claude/agents/plan-reviewer.md`) **in foreground**, passing the filled **For Subagent** section as the prompt — one-shot, evaluates against 13 dimensions, returns findings. **Run in foreground** (not background) unless you have independent work to do in parallel during review — foreground gives progress visibility and avoids redundant launches if the agent appears stalled.

If review has FAILs:
- Revise the plan files on disk yourself (you have full context from plan design)
- Re-spawn the reviewer (max 2 revision rounds)
- If still failing after 2 rounds: present findings to user, ask how to proceed

## Phase E: Final Review & Finalization

### Step 9: Final User Review

Present the plan to the user after automated review passes:

1. Use the CLI to display the plan summary. Show specific phase details if the user wants depth.
2. User can: **approve**, **request changes**, or **reject**
3. If changes requested: revise files on disk, re-run automated review (Step 8)
4. If rejected: inform user plan remains as draft in `$PLAN_DIR`
5. If approved: proceed to Step 10

### Step 10: Finalize Plan

**If creating multiple plans in one session:** Complete Step 10 fully for each plan before starting the next. Each plan gets its own `$PLAN_DIR`. Do NOT interleave.

1. Use the CLI to set plan status to "approved"
2. **MANDATORY:** Use the CLI to initialize state (creates `state.json` from plan + phase files). Do NOT write state.json manually.
3. Tell the user: "Plan approved at `$PLAN_DIR`. Run `/execute` to start implementation."
4. Use the CLI to display the initial execution state

## Phase F: Post-Planning Knowledge Update

Merge findings from Phase A and Phase B, present actionable items to the user, and apply approved updates.

### Step 11: Merge & Present Findings

1. Collect the **Corrections Log** from Phase A (Step 3) and the **Findings Log** from Phase B (Step 4b)
2. Merge both tables into a single list, deduplicate entries that reference the same contradiction
3. **If the merged list is empty ("None" in both logs):** skip Phase F entirely — tell the user "No documentation contradictions found during planning." and proceed to hand off.
4. **If findings exist:** present each to the user:

For each finding:
- "During planning, I found: **{finding/correction}**"
- "Current doc says: {what the doc states} | Reality: {what's actually true}"
- "Target: **{target doc path}**"
- "Proposed update: {specific change}"

Ask the user: "Apply these updates? (approve all / select which / skip all)"

### Step 12: Apply Approved Updates

For each approved finding, apply based on target:

| Target | Action |
|--------|--------|
| `.analysis.md` — behavioral finding | Add row to **Hidden Details** table |
| `.analysis.md` — rationale finding | Add row to **Design Decisions** table |
| `.workflow/project-overview.md` | Patch the relevant section |
| `.workflow/rules/planning/*.md` or `rules/code/*.md` | Create or update rule file |

For `.analysis.md` patches: also update `last_analyzed` to today's date. Do NOT update `source_hash` (source didn't change — only the analysis doc is being enriched with planning knowledge).

## Questions This Skill Answers

- "/plan [requirements]"
- "Break this down into tasks"
- "Create a plan for [feature]"
- "Plan from this GitHub issue / gh:123"
- "Plan from jira:PROJ-456"
