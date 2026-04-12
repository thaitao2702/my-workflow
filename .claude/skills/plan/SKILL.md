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

Analyze requirements for gaps and ambiguities. **Think deeply before asking — don't ask surface-level questions.**

1. Read `.workflow/project-overview.md` for architectural context

2. **Self-check before generating questions.** Ask yourself:
   - Are there implicit requirements the user assumes but didn't state? (auth, validation, error handling, permissions)
   - What data sources, dependencies, or external systems are needed but not mentioned?
   - What scenarios would break this? What are the unhappy paths and edge cases?
   - Where does this feature's scope END? What's explicitly NOT included?

3. Generate specific, concrete clarification questions based on the self-check. Examples:
   - "The export feature — should it support CSV only, or also Excel/PDF?"
   - "When the payment fails, should the order stay pending or be cancelled?"
   - NOT: "Can you tell me more about the requirements?" (too open-ended)

4. Present questions to user, wait for answers
5. Loop until no more genuine gaps (max 3 clarification rounds)

6. **After clarification rounds complete**, check if the user corrected any assumptions that contradict existing documentation. If so, record them:

**Corrections Log:**
| Correction | Source | Contradicts | Target Doc |
|-----------|--------|-------------|------------|

Only record corrections where existing documentation (analysis docs, project-overview) says something different from what the user clarified. Not new requirements — contradictions of existing documented knowledge. Examples:
- User says "that service doesn't handle retries anymore" but analysis doc says it does → record
- User says "the feature should support CSV export" (new requirement) → don't record

If no corrections: write "None" under the table header.

If after self-check you have no real questions — requirements are clear and complete — skip directly to Phase B.

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

4. **Note what you learn.** Capture key findings that will shape the plan: constraints, hidden behaviors, integration points, existing patterns to follow. These populate `component_intelligence` in Step 7.

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

## Phase C: Plan Creation (Main Agent)

You design the plan directly — no subagent delegation. All context from Phases A-B is already in your session.

**Read `.claude/skills/plan/planning-reference.md` now.** It contains the planning principles, decision classification guide, and generation constraints that govern Steps 5-7. Apply them throughout Phase C.

### Step 5: Problem Decomposition & Approach Design

Design the plan through layered reasoning — decompose first, then analyze each piece, then compose into phases. Process one layer at a time; commit decisions before descending to the next layer.

#### Step 5a: Capability Decomposition

From requirements + clarification answers + component intelligence, identify the distinct capabilities this plan needs to deliver. Each capability is an independent functional unit that delivers user-visible or system-visible value.

Output a numbered list, one capability per line with a brief description:

```
### Capabilities
1. [Capability name] — [what it does, one line]
2. [Capability name] — [what it does, one line]
3. ...
```

Rules:
- Aim for MECE (mutually exclusive, collectively exhaustive) — no overlaps, no gaps
- Each capability should be describable in one sentence
- If a requirement maps to a single obvious capability, that's fine — not everything needs decomposition
- If you identify more than 7 capabilities, group related ones into domains first

**Complexity gate:** If there is only 1-2 capabilities with obvious approaches (no significant architectural decisions), collapse Steps 5b-5c into a brief note: "Approach: [description], follows existing [convention/pattern]" — then skip directly to Step 5d.

#### Step 5b: Per-Capability Analysis & Approach Selection

Process capabilities **one at a time**. Output the full analysis for each capability before moving to the next. This forces step-by-step reasoning and prevents combinatorial explosion.

**For each capability, output this block:**

```
### Capability N: [Name]

**Core problem:** [What's the actual technical challenge? 1-2 sentences]

**Decisions:**
| Decision | Classification | Rationale |
|----------|---------------|-----------|
| [what needs deciding] | Constrained / Conventional / Significant | [why this classification — cite constraint source, convention, or the cascade that makes it significant] |

[IF significant decisions exist:]

**Approach evaluation: [decision name]**
| Approach | What | Key Trade-off | Fit |
|----------|------|---------------|-----|
| [name] | [1-line description] | [main pro vs con] | [fit with project context] |
| [name] | [1-line description] | [main pro vs con] | [fit with project context] |

**Selected:** [approach] — [1-line rationale]

**Committed approach:** [1-line summary of how this capability will be built]
```

Rules:
- **Decide-then-descend:** the "Selected" and "Committed approach" lines are mandatory before moving to the next capability. No open options carried forward.
- **Classify before branching:** apply the decision classification filter (see `planning-reference.md`) to every decision. Only significant decisions get approach evaluation.
- **Cascade check:** before classifying a decision as constrained/conventional, trace its implications — does the choice cascade into phase-level changes? If yes, it's significant regardless of how "obvious" it seems.
- **Max 3 approaches** per significant decision. If you see more, you're decomposing at the wrong level.
- Later capabilities can reference earlier committed decisions: "Given Cap 1's selection of [X], this constrains the approach to..."

#### Step 5c: Phase Composition

All capabilities have committed approaches. Now compose them into phases:

1. **Group capabilities into phases** — by cohesion, dependency order, and parallel safety. A single capability may span multiple phases if it has natural sequential stages.
2. **Identify integration tasks** — what connects the capabilities at runtime? If Phase A produces an artifact that Phase B consumes, there must be a task that wires them. Don't assume integration happens by itself.
3. **Trace end-to-end flow** — from user action through all phases to system response. Every transition must be covered by a task. Gaps here = gaps in the plan.
4. **Check dependency ordering** — producers before consumers, no circular deps, interface dependencies enforce sequential groups.

#### Step 5d: Direction Summary

Synthesize the decomposition into a **direction summary** for user validation:

- Plan name and scope
- Number of phases and total tasks
- Phase overview with dependency groups and key dependencies
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
- Top risks

Do NOT produce full JSON at this point — just the direction for user validation.

### Step 6: User Direction Checkpoint

The user understands the requirements better than any agent — catching directional mistakes here is cheap; running a 12-dimension review on a plan the user would reject is waste.

1. Present the direction summary to the user
2. Ask: "Does this direction look right? Approve to proceed, or tell me what to change."
3. If user wants changes:
   - If the user disagrees with a key decision from the table, re-enter Step 5b for that specific capability only — don't redo the entire analysis
   - For structural changes (add/remove phases, change grouping), revise Step 5c-5d
   - Present the updated direction summary and ask again
   - Repeat until user approves direction
4. If user approves: proceed to Step 7

### Step 7: Write Plan Files

Direction approved — now materialize the full plan to disk.

**Read `.claude/skills/plan/plan-phase-formats.md` now.** It contains the `plan.json` and `phase-{N}.json` format specifications with all field definitions. Follow these formats for sub-steps 2-5.

1. Create directory: `.workflow/plans/{YYMMDD}-{slug}/`
   - `{YYMMDD}` = today's date (e.g., `260328`)
   - `{slug}` = kebab-case from plan name
   - **Store as `$PLAN_DIR`** — all subsequent CLI calls use `--plan-dir $PLAN_DIR`

2. Write `plan.json` with `"status": "draft"` following the plan file format
3. Write `phase-{N}.json` for each phase following the phase file format
4. **Write acceptance specs:** For each phase, derive `acceptance_specs` that verify the phase delivers its requirements. Review each phase's tasks against the overall `scope.in_scope` requirements. Every requirement should trace to at least one spec across all phases. Write specs into the phase JSON files. Specs should cover functional correctness — not code quality (that's the reviewer's job).
5. **Identify and declare cross-phase dependencies:** Scan all phases for cross-phase code dependencies — any place where Phase X's code imports, calls, or receives objects created by Phase Y. For each dependency:
   a. Identify the **defining phase** (the one that creates the class or module)
   b. Add an `interface_contracts` entry to that phase's JSON: contract ID, expected class name, purpose description, defined_in_task, consumed_by_phases
   c. In the **consuming phase's** task description, add a contract reference: "Receives BridgeHelper (Phase 3 contract-01) via constructor injection"
   d. **Enforce sequential ordering:** verify that the defining phase is in an earlier execution group than ALL consuming phases listed in consumed_by_phases. If not, move the consuming phase to a later group.
   Only cross-phase interfaces need declarations — internal functions within a single phase are the executor's domain.
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
