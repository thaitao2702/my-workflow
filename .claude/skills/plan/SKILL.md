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

**Component Intelligence:** analysis doc freshness (fresh/stale/missing), progressive loading level (0/1/2), component role classification (Modified/Extended/Consumed/Created), analysis gate, knowledge layer

**Quality Assurance:** plan review (10-dimension evaluation), direction checkpoint (Step 6), revision round (max 2), automated review before user review

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
- **Resolution:** Always produce a brief direction summary (Step 5) and get user approval (Step 6) before writing plan files (Step 7). Catching directional mistakes early is cheap; rewriting a reviewed plan is expensive.

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

You design the plan directly — no subagent delegation. All context from Phases A-B is already in your session. Use the planning principles below and the format specs to design a quality plan.

### Planning Principles

These principles govern plan design during Steps 5-7.

#### Phase Sizing
Each phase spawns one executor subagent that implements all tasks sequentially. All tasks in a phase must fit in one agent session. If the phase is too large, split into more phases — not more granular tasks.

#### Task Granularity — The Coherent Unit
A task is the unit of progress tracking — the executor marks each task complete for resume. This means:

- **Lower bound:** A task must be a meaningful unit of progress worth tracking independently. A 2-line change doesn't need its own task. Merge trivially small changes (one import, one hook call, one type declaration) with related tasks.
- **Cohesion:** Tightly coupled changes belong in ONE task. If change A only makes sense because of change B, they're one task:
  - Type declaration + the class that uses it → one task
  - Public accessor + the code that calls it → one task
  - Two 1-line hooks in different files for the same concern → one task
- **The test:** Would a developer naturally do these changes in one sitting, one commit? If yes → one task.

**Bad granularity (9 tasks):**
- task-01: Create base class (1 file)
- task-02: Create type declaration (3 lines) ← too small, coupled with task-01
- task-05: Add accessor to CellView (2 lines)
- task-06: Use accessor in HoldSpinView (2 lines) ← coupled with task-05

**Good granularity (5 tasks, same work):**
- task-01: Create base class + type declaration (cohesive: type references the class)
- task-02: Implement bridge + activator (cohesive: activator instantiates bridge)
- task-03: CellView accessor + HoldSpinView wiring (cohesive: accessor exists for the wiring)

#### Task Descriptions — WHAT and WHY, Never HOW
Tasks describe **WHAT to build and WHY** — constraints, boundaries, purpose. The executor decides HOW by reading source code and analysis docs.

- **Good:** "Create abstract base class for test bridges. Must be pure TypeScript with zero engine imports. Methods: register, waitForState (polling-based), getSnapshot. See component analysis for existing patterns."
- **Bad:** "Create TestBridgeBase.ts. Method waitForState: polls getAppState() every 200ms using setInterval, resolves when state matches, rejects after timeout."

The bad example leaks implementation (polling interval, exact property paths) into the plan. The executor discovers these by reading source code — pre-deciding means the planner guesses and the executor follows blindly.

#### Plan Summary as Mission Briefing
The `summary` field is the executor's primary orientation document. Every executor reads it before starting any task. It must answer: What are we building? Why? What are the key constraints and architectural decisions? What should the executor know that ISN'T in individual task descriptions?

Test: "If a new developer reads the summary + a task description, can they implement correctly?"

#### Acceptance Criteria
Every criterion must be **verifiable by running something** — a test, a command, a query. "Works correctly" is NOT verifiable. "GET /api/reports returns 200 with JSON array matching ReportSchema" IS. If you can't write a verifiable criterion, the task isn't well-defined enough.

#### Acceptance Specifications
Acceptance specifications (`acceptance_specs`) are **phase-level** verification targets consumed by an independent verifier after execution — distinct from task-level `acceptance_criteria`:

| Concept | Level | Consumer | Purpose |
|---------|-------|----------|---------|
| `acceptance_criteria` | Per-task | Executor | Definition-of-done during implementation |
| `acceptance_specs` | Per-phase | Acceptance verifier (post-execution) | Independent behavioral verification |

- Specs are derived from **requirements**, not from tasks — a spec may span multiple tasks via `traces_to`
- `verify_by` must be concrete enough for either a test author (write + run test code) or a reasoning agent (read code and trace behavior) to determine PASS/FAIL unambiguously
- Every requirement in `scope.in_scope` should trace to at least one `acceptance_spec` across all phases
- Specs verify **functional correctness** (does it work?), not code quality (that's the reviewer's job)

#### Using Component Intelligence
Hidden details in analysis docs often reveal constraints that change the plan. If a component silently clamps date ranges to 90 days, your "export all data" feature needs pagination. Reference specific findings in `component_intelligence` so reviewers understand why you made certain choices.

#### Parallel Safety
Assign parallel groups (A, B, C...) to phases that can run simultaneously. **The #1 rule:** phases in the same group must NOT modify the same files — this prevents merge conflicts. When in doubt, put phases in separate groups. Sequential is safe; parallel is fast but risky.

### Step 5: Design Plan Direction

Design the plan using:
- Gathered context (requirements, clarification answers — already in your session)
- Component analysis (`.analysis.md` artifacts verified in Step 4b)
- Project overview (`.workflow/project-overview.md`)
- Planning principles above
- JSON format specs defined in Step 7 (plan.json and phase-{N}.json structures)

Produce a **brief direction summary** (10-15 lines):
- Plan name and scope
- Number of phases and total tasks
- Phase overview with dependency groups and key dependencies
- Key architectural decisions that shaped the plan
- Top risks

Do NOT produce full JSON at this point — just the direction for user validation.

### Step 6: User Direction Checkpoint

The user understands the requirements better than any agent — catching directional mistakes here is cheap; running a 10-dimension review on a plan the user would reject is waste.

1. Present the direction summary to the user
2. Ask: "Does this direction look right? Approve to proceed, or tell me what to change."
3. If user wants changes:
   - Incorporate the feedback — adjust phases, scope, dependencies, or architecture as needed
   - Produce an updated direction summary (same format as Step 5 output)
   - Present it to the user and ask again
   - Repeat until user approves direction
4. If user approves: proceed to Step 7

### Step 7: Write Plan Files

Direction approved — now materialize the full plan to disk.

1. Create directory: `.workflow/plans/{YYMMDD}-{slug}/`
   - `{YYMMDD}` = today's date (e.g., `260328`)
   - `{slug}` = kebab-case from plan name
   - **Store as `$PLAN_DIR`** — all subsequent CLI calls use `--plan-dir $PLAN_DIR`

2. Write `plan.json` with `"status": "draft"` following the plan file format below
3. Write `phase-{N}.json` for each phase following the phase file format below
4. **Write acceptance specs:** For each phase, derive `acceptance_specs` that verify the phase delivers its requirements. Review each phase's tasks against the overall `scope.in_scope` requirements. Every requirement should trace to at least one spec across all phases. Write specs into the phase JSON files. Specs should cover functional correctness — not code quality (that's the reviewer's job).
5. Use the CLI to read back the plan and verify files written correctly

### Plan File Format: `plan.json`

```json
{
  "name": "{feature-name}",
  "created": "{YYYY-MM-DD}",
  "status": "draft",
  "total_phases": 3,
  "total_tasks": 12,
  "summary": "Mission briefing — see field definition below",
  "scope": {
    "in_scope": ["requirement 1", "requirement 2"],
    "out_of_scope": ["explicitly excluded item"]
  },
  "component_intelligence": "Key findings from analysis that shaped this plan",
  "phases": [
    {"phase": 1, "name": "Database schema", "tasks": 3, "dependencies": [], "group": "A"},
    {"phase": 2, "name": "API endpoints", "tasks": 4, "dependencies": [1], "group": "B"},
    {"phase": 3, "name": "UI components", "tasks": 5, "dependencies": [1], "group": "B"}
  ],
  "dependency_graph_mermaid": "graph TD\n  P1-->P2\n  P1-->P3\n  P2-->P4\n  P3-->P4",
  "risks": [
    {"risk": "description", "impact": "high|med|low", "mitigation": "strategy"}
  ]
}
```

**Field definitions:**
- `name`: kebab-case feature identifier, used for directory naming
- `status`: `draft` → `reviewed` → `approved` → `executing` → `completed`
- `summary`: Mission briefing for the executor — see "Plan Summary as Mission Briefing" principle above. Target: ~200-400 tokens.
- `scope.in_scope` / `out_of_scope`: explicit boundaries to prevent scope creep during execution
- `component_intelligence`: Key findings from analysis that shaped plan choices — see "Using Component Intelligence" principle above.
- `phases[].dependencies`: array of phase numbers that must complete BEFORE this phase starts. Drives execution ordering.
- `phases[].group`: Parallel execution group letter (A, B, C...). Phases in the same group run simultaneously — see "Parallel Safety" principle above.
- `dependency_graph_mermaid`: Mermaid diagram string showing phase dependencies visually
- `risks`: informed by component analysis hidden details — what could go wrong, how to mitigate. Each risk should have a concrete mitigation the executor can follow.

### Phase File Format: `phase-{N}.json`

```json
{
  "phase": 1,
  "name": "Database schema",
  "status": "pending",
  "group": "A",
  "depends_on": [],
  "affected_components": ["src/models/user.ts", "src/models/order.ts"],
  "goal": "Phase briefing — see field definition below",
  "tasks": [
    {
      "id": "task-01",
      "name": "Create users table",
      "description": "What to do — describes WHAT and WHY, not HOW",
      "files": ["src/db/migrations/001_users.sql", "src/models/user.ts"],
      "acceptance_criteria": [
        "Users table exists with id, email, role columns",
        "RLS policies enforce account isolation"
      ],
      "test_requirements": [
        "Insert and select user succeeds",
        "Cross-account select returns empty"
      ]
    }
  ],
  "acceptance_specs": [
    {
      "id": "spec-01",
      "description": "Account isolation enforced at database level",
      "traces_to": ["task-01"],
      "verification_type": "functional",
      "verify_by": "INSERT user under account A, SELECT under account B returns empty result set"
    }
  ]
}
```

**Field definitions:**
- `group`: same as in plan.json — parallel execution group. Must match.
- `depends_on`: phase numbers that must complete first. Must match plan.json dependencies.
- `affected_components`: file paths of components this phase touches — used by `/doc-update` during reconciliation
- `goal`: **Phase briefing.** What this phase achieves and why it matters in the overall plan. An executor starting this phase should understand: what the phase produces, how it connects to other phases, what constraints apply. Include context that's specific to this phase but not repeated in every task. (e.g., "After this phase, the bridge contract is defined and any game can extend it. All files are pure TypeScript — zero engine imports.") Target: 2-4 sentences.
- `tasks[]`: Coherent units of work — see "Task Granularity" principle above. Each is the unit of progress tracking (executor marks complete for resume).
- `tasks[].id`: Unique within the phase, format `task-NN`
- `tasks[].description`: WHAT and WHY, never HOW — see "Task Descriptions" principle above. Exclude: property paths, method signatures, implementation code, line numbers.
- `tasks[].files`: Files to create or modify — used for parallel safety checks (see "Parallel Safety" above)
- `tasks[].acceptance_criteria`: Verifiable conditions — see "Acceptance Criteria" principle above.
- `tasks[].test_requirements`: Specific tests to write — not "write tests" but "test that expired tokens return 401"
- `acceptance_specs[]`: Phase-level verification targets for the independent acceptance verifier — see "Acceptance Specifications" principle above.
- `acceptance_specs[].id`: Unique within phase, format `spec-NN`
- `acceptance_specs[].description`: What behavior or property must hold. One sentence.
- `acceptance_specs[].traces_to`: Array of task-ids whose combined implementation satisfies this spec. For requirement traceability.
- `acceptance_specs[].verification_type`: `functional` (run + check output) | `structural` (code pattern must exist) | `behavioral` (system exhibits behavior under scenario)
- `acceptance_specs[].verify_by`: Concrete verification scenario. Must enable unambiguous PASS/FAIL determination. Framework-agnostic — no test framework syntax. In test mode this guides what test code to write; in reason mode this is the reasoning target.

## Phase D: Quality Review

### Step 8: Automated Review

Read the prompt template: `.claude/skills/plan/plan-reviewer-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions and review dimensions
3. Spawn a **plan-reviewer subagent** (`.claude/agents/plan-reviewer.md`), passing the filled **For Subagent** section as the prompt — one-shot, evaluates against 11 dimensions, returns findings

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
