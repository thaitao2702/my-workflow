---
description: "Create an execution plan from requirements — phases, tasks, dependency graph, quality review"
---

# /plan — Create Execution Plan

You are creating a detailed, dependency-aware, quality-checked execution plan. Transform requirements into phased tasks that an executor agent can implement.

**Input:** `/plan "requirement text"`, `/plan ./path/to/requirements.md`, `/plan gh:123`, or `/plan jira:PROJ-456`
**Output:** `.workflow/plans/{YYMMDD}-{name}/` directory with `plan.json`, phase JSON files, and `state.json`

## Phase A: Requirement Gathering

### Step 1: Parse Input

Determine the input source and extract requirements:

| Input Pattern | Action |
|--------------|--------|
| `"quoted text"` or plain text | Use directly as requirements |
| `./path/to/file.md` | Read the file, extract requirements |
| `gh:123` or GitHub URL | Run `gh issue view 123 --json title,body,comments` and extract |
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
2. From requirements + project overview, identify **candidate affected areas** — which modules, domains, or features from the project overview are likely involved. You don't know specific files yet — use the modules/domains table and core flows from the overview to identify areas.
3. For each candidate area, check if an `.analysis.md` file exists **in the same directory** as the component source file (e.g., `src/services/authService.ts` → check for `src/services/authService.analysis.md`). If it exists, note it — you'll use it in Phase B. Do NOT read it yet, and do NOT glob subdirectories — analysis docs are co-located with their source file, not nested.

4. **Self-check before generating questions.** Ask yourself:
   - Do I genuinely understand every requirement well enough to break it into concrete tasks?
   - Are there implicit requirements the user assumes but didn't state? (auth, validation, error handling, permissions)
   - What input does this feature need that isn't specified? What's the source of data?
   - What scenarios would break this? What's the unhappy path?
   - Does this feature depend on anything external not mentioned? (APIs, services, configs)
   - Can this design serve all use cases, or is there a case that makes it fall apart?
   - Where does this feature's scope END? What's explicitly NOT included?

5. Generate specific, concrete clarification questions based on the self-check. Examples:
   - "The export feature — should it support CSV only, or also Excel/PDF?"
   - "When the payment fails, should the order stay pending or be cancelled?"
   - NOT: "Can you tell me more about the requirements?" (too open-ended)

6. Present questions to user, wait for answers
7. Loop until no more genuine gaps (max 3 clarification rounds)

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

1. **Check if `.analysis.md` exists** alongside the source (noted in Phase A Step 3).

2. **If `.analysis.md` exists — verify freshness:**
   - Compute hash of the component's `entry_files`: `python .claude/scripts/workflow_cli.py hash {entry_files}`
   - Compare with `source_hash` in the analysis frontmatter
   - If `dependency_tree` exists in frontmatter, also hash those dependency files and compare
   - **All hashes match (fresh):** read the `.analysis.md` as your primary source. It contains purpose, public API, hidden behaviors, edge cases, integration patterns, and accumulated experience from prior implementations. Judge whether this gives you enough to plan — if yes, skip source. If you need more detail (e.g., exact internal flow for a complex modification), read source selectively.
   - **Any hash mismatch (stale):** skip the analysis doc — read source directly instead.

3. **If no `.analysis.md` exists:** read source directly.

4. **What to read from source** (when falling back):
   - Modified/Extended components: read thoroughly — every function, not just exports
   - Consumed components: focus on public API / exports
   - Created components: read source of similar existing components for reference patterns

5. **Note what you learn.** Capture key findings that will shape the plan: constraints, hidden behaviors, integration points, existing patterns to follow. These populate `component_intelligence` in Step 7.

**Do NOT invoke `/analyze` during planning.** If an analysis doc is stale or missing, read source directly. Analysis generation is expensive (subagent overhead) and best deferred to the execution analysis gate (Step 2a in `/execute`).

## Phase C: Plan Creation (Main Agent)

You design the plan directly — no subagent delegation. All context from Phases A-B is already in your session. Use the planning principles below and the format specs to design a quality plan.

### Planning Principles

These principles govern plan design during Steps 5-7.

#### Task Granularity — The Coherent Unit
Each phase spawns one executor subagent that implements all tasks sequentially, tracking each task's completion for resume. This means:

- **Upper bound:** All tasks in a phase must fit in one agent session. If the phase is too large, split into more phases — not more granular tasks.
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
4. Use the CLI to read back the plan and verify files written correctly

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
- `summary`: **Mission briefing for the executor.** This is the primary guidance document — an executor agent reading ONLY this summary + a task description should understand enough to implement correctly. Include:
  - What we're building and why (the goal, not just the feature name)
  - Key architectural decisions and constraints ("polling only, no events", "activated by URL param only", "reads internal state but never modifies game logic")
  - Important context that affects HOW tasks should be implemented ("bridge must have zero cost when not activated", "all state reads go through GlobalContext singletons")
  - Relationships to other systems if relevant ("QA platform depends on bridge-api.md output")
  - NOT implementation details (no property paths, no method signatures — those belong in analysis docs and source code)
  - Target: ~200-400 tokens. Rich enough to guide, concise enough to include in every executor prompt.
- `scope.in_scope` / `out_of_scope`: explicit boundaries to prevent scope creep during execution
- `component_intelligence`: key findings from pre-planning analysis that explain WHY the plan makes certain choices. These are facts discovered during component analysis that the executor needs to know — edge cases, hidden constraints, non-obvious behaviors. (e.g., "AutoPopup.onConfirmClicked() is private — use onConfirm callback instead", "numberAutoSpin uses -1 as disabled sentinel, Infinity as unlimited")
- `phases[].dependencies`: array of phase numbers that must complete BEFORE this phase starts. Drives execution ordering.
- `phases[].group`: parallel execution group letter (A, B, C...). **Phases in the same group run simultaneously.** This means they MUST NOT modify the same files — file conflicts in parallel execution cause merge failures. Group A runs first, then all of group B in parallel, then group C, etc.
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
  ]
}
```

**Field definitions:**
- `group`: same as in plan.json — parallel execution group. Must match.
- `depends_on`: phase numbers that must complete first. Must match plan.json dependencies.
- `affected_components`: file paths of components this phase touches — used by `/doc-update` during reconciliation
- `goal`: **Phase briefing.** What this phase achieves and why it matters in the overall plan. An executor starting this phase should understand: what the phase produces, how it connects to other phases, what constraints apply. Include context that's specific to this phase but not repeated in every task. (e.g., "After this phase, the bridge contract is defined and any game can extend it. All files are pure TypeScript — zero engine imports.") Target: 2-4 sentences.
- `tasks[]`: Each task is a **coherent unit of work** — meaningful enough to track independently (the executor marks each complete for resume), small enough that all tasks in the phase fit in one agent session. Tightly coupled changes (type + class, accessor + consumer, multiple hooks for the same concern) belong in ONE task. A 2-line change should NOT be its own task.
- `tasks[].id`: unique within the phase, format `task-NN`
- `tasks[].description`: **WHAT to do and WHY.** The executor decides HOW to implement by reading source code and analysis docs. Description should include:
  - What to create or modify
  - Why this task exists (its purpose in the phase)
  - Constraints and boundaries ("zero engine imports", "no-op when bridge inactive")
  - Which components to reference for patterns
  - Do NOT include: exact property paths, method signatures, implementation code, line numbers. Those belong in `.analysis.md` docs and source code — the executor reads them directly.
- `tasks[].files`: files to create or modify — used for file scope safety checks (parallel phases can't touch same files)
- `tasks[].acceptance_criteria`: **verifiable** conditions. Each must be testable by running something (a test, a command, a query). "Works correctly" is NOT verifiable. "Returns 200 with JSON matching schema" IS.
- `tasks[].test_requirements`: specific tests to write — not "write tests" but "test that expired tokens return 401"

## Phase D: Quality Review

### Step 8: Automated Review

Read the prompt template: `.claude/skills/plan/plan-reviewer-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions and review dimensions
3. Spawn a **reviewer subagent** (`.claude/agents/reviewer.md`), passing the filled **For Subagent** section as the prompt — one-shot, evaluates against 10 dimensions, returns findings

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

## Phase F: Post-Planning Reflection

Before handing off to the user, reflect on what was learned during the planning process. **Skip this step entirely if nothing significant was discovered.**

### What to look for

During Phase B (component analysis) and Phase C (plan creation), you may have discovered things that contradict or are missing from existing documentation:

- **Component analysis revealed hidden behaviors** not documented in `.analysis.md` → those should already be captured by `/analyze`. But if you noticed something the analyzer missed (e.g., a cross-component interaction only visible when planning the feature), that's a finding.
- **Requirements contradicted existing architecture** → the plan adapted, but the architectural assumption that led to the contradiction might affect future plans too.
- **Project overview was inaccurate** → a module described as "handles X" actually also handles Y, or the data flow diagram is wrong.
- **An assumption about a component turned out wrong during clarification** → the user corrected something that the code alone couldn't reveal (business logic, external constraints).

### What to do

Only for **non-trivial findings** that could cause problems in future plans or execution:

1. Present each finding to the user:
   - "During planning, I discovered: {finding}"
   - "This should be documented in: {target document}"
   - "Proposed update: {specific content to add/change}"
2. If user agrees: apply the update to the appropriate document:
   - Component-specific → update `.analysis.md` Hidden Details table
   - Pattern-level → create/update rule in `.workflow/rules/planning/` or `code/`
   - Architecture-level → update `.workflow/project-overview.md`
3. If user disagrees or finding is trivial: skip it.

**Skip criteria:** Don't surface findings that are:
- Already captured by the analysis docs (redundant)
- Trivial or obvious from the code
- Specific to this one plan with no future relevance

## Constraints
- Do NOT delegate plan creation to a subagent — design the plan directly in the main session (you have full context from Phases A-B)
- Do NOT include implementation code in the plan — tasks describe WHAT, executor decides HOW
- Do NOT create more than 5 phases unless the feature genuinely requires it
- Do NOT create phases with more tasks than an executor can complete in one agent session
- Do NOT put tasks that modify the same files in the same parallel group
- Do NOT skip the user direction checkpoint (Step 6) — validate direction before writing files
- Do NOT skip the automated review (Step 8) — the reviewer subagent catches structural issues
- Do NOT proceed past user review without explicit approval
- Do NOT write state.json manually — always use the CLI to initialize state
- Do NOT update plan status manually — always use the CLI to set status
- Do NOT run CLI commands without `--plan-dir $PLAN_DIR` (when plan files exist on disk)
