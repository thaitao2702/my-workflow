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
3. For each candidate area, check if the specific component already has an `.analysis.md` file **in the same directory** as the component source file (e.g., `src/services/authService.ts` → check for `src/services/authService.analysis.md`). If it exists, read its frontmatter for additional context. Do NOT glob subdirectories — analysis docs are co-located with their source file, not nested.

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

### Step 4: Identify Affected Components

From requirements + project overview + clarification answers, identify specific components and classify their role:

| Role | Meaning | Analysis Depth |
|------|---------|---------------|
| **Modified** | Changing its internals | **Deep** (recursive) — you're touching the wiring, need to understand dependencies |
| **Extended** | Adding new features to it | **Deep** (recursive) — you're adding to the machine, need to understand the parts |
| **Consumed** | Calling its API from new code | **Shallow** (single component) — you're a caller, just need the contract |
| **Created** | New component, checking similar existing ones | **Shallow** (single component) — looking for a reference pattern |

**During this step:** You may browse the codebase to identify the right component paths (using Glob, Grep). But the purpose of this step is to identify WHICH components need analysis and ensure `.analysis.md` artifacts exist — not to deeply read source code yourself. The analysis agent does the deep reading.

### Step 4a: Run Analysis for Each Component

For each affected component:

1. Check if `{component}.analysis.md` exists alongside the source
2. If exists: read **frontmatter only** (first ~10 lines), compare `last_commit` vs `git log -1 --format=%H -- {entry_files}`
   - **Current** → analysis exists and is up to date. Skip.
   - **Stale** → needs re-analysis. Proceed to invoke below.
3. If doesn't exist → needs analysis. Proceed to invoke below.

**Invoking analysis based on component role:**

- **Modified / Extended** components (deep): use the Skill tool to invoke `/analyze {component-path} --recursive`
  - Before invoking, check how many dependencies lack `.analysis.md`:
    - **0-2 missing** → proceed with deep analysis automatically
    - **3+ missing** → warn the user: "Component {name} has {N} unanalyzed dependencies. Deep analysis is recommended but will take time. Proceed with deep / shallow / skip?"
  - User can override to shallow if they judge the dependencies are irrelevant to the planned changes
- **Consumed / Created** components (shallow): use the Skill tool to invoke `/analyze {component-path}` (no --recursive flag)

**MANDATORY: You MUST invoke `/analyze` via the Skill tool for every component that has no up-to-date `.analysis.md`. Do NOT substitute direct file reads for this step.** The analysis produces a structured, persistent artifact that downstream steps depend on.

### Step 4b: Verify Analysis Artifacts

**After all analysis invocations complete, verify before proceeding:**

For EVERY affected component (modified, extended, consumed, created):
1. Check: does `{component}.analysis.md` exist on disk?
2. Check: read frontmatter — is `last_commit` current vs `git log -1 --format=%H -- {entry_files}`?
3. Check: are `name`, `type`, `summary`, `entry_files` populated?

**If ANY component fails this check → STOP. Invoke `/analyze` for the failing component. Re-run this check.**

Do NOT proceed to Step 5 until all checks pass.

## Phase C: Plan Creation

### Step 5: Spawn Planner Agent

Use the Agent tool to spawn a subagent with `.claude/agents/planner.md`.

Provide the agent with:
1. **Finalized requirements** (from Step 1-3)
2. **Project overview** — `.workflow/project-overview.md`
3. **Component analysis docs** — read the `.analysis.md` files **fresh from disk** (Level 1: frontmatter + CONTENT section). Verified in Step 4b.
4. **Source code of key files** — for Modified/Extended components, include the actual source files. The `.analysis.md` gives the planner the component's API and hidden details, but source code lets the planner judge implementation feasibility (e.g., "can this function be extended to also handle X?").
5. **Template context** (if `/template-apply` was used in Step 2)
6. **Config** — `.workflow/config.json`
7. **The plan and phase JSON formats below** — including field definitions

The planner agent returns: structured plan data + phase data.

### Plan File Format: `plan.json`

```json
{
  "name": "{feature-name}",
  "created": "{YYYY-MM-DD}",
  "status": "draft",
  "total_phases": 3,
  "total_tasks": 12,
  "summary": "What we're building and why — 2-3 sentences",
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
- `summary`: concise description of what and why — used as context for all downstream agents
- `scope.in_scope` / `out_of_scope`: explicit boundaries to prevent scope creep during execution
- `component_intelligence`: key findings from pre-planning analysis that explain WHY the plan makes certain choices (e.g., "date range clamped to 90 days server-side, so export needs pagination")
- `phases[].dependencies`: array of phase numbers that must complete BEFORE this phase starts. Drives execution ordering.
- `phases[].group`: parallel execution group letter (A, B, C...). **Phases in the same group run simultaneously.** This means they MUST NOT modify the same files — file conflicts in parallel execution cause merge failures. Group A runs first, then all of group B in parallel, then group C, etc.
- `dependency_graph_mermaid`: Mermaid diagram string showing phase dependencies visually
- `risks`: informed by component analysis hidden details — what could go wrong, how to mitigate

### Phase File Format: `phase-{N}.json`

```json
{
  "phase": 1,
  "name": "Database schema",
  "status": "pending",
  "group": "A",
  "depends_on": [],
  "affected_components": ["src/models/user.ts", "src/models/order.ts"],
  "goal": "What this phase achieves — 1-2 sentences",
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
- `goal`: what this phase achieves as a unit — should be independently testable
- `tasks[].id`: unique within the phase, format `task-NN`
- `tasks[].description`: what to do and why — the executor decides HOW to implement
- `tasks[].files`: files to create or modify — used for file scope safety checks (parallel phases can't touch same files)
- `tasks[].acceptance_criteria`: **verifiable** conditions. Each must be testable by running something (a test, a command, a query). "Works correctly" is NOT verifiable. "Returns 200 with JSON matching schema" IS.
- `tasks[].test_requirements`: specific tests to write — not "write tests" but "test that expired tokens return 401"

## Phase D: Plan Review

### Step 6: Automated Review

Use the Agent tool to spawn a subagent with `.claude/agents/reviewer.md`.

Provide the agent with:
1. **The plan** — pass the plan data and phase data directly from the planner agent's output (in-memory from Step 5). Do NOT read from disk — the files have not been written yet.
2. **The 8 review dimensions** — include this list explicitly in the agent's prompt so it knows exactly what to check:
   1. **Requirement coverage** — every requirement maps to at least one task
   2. **Task atomicity** — each task is completable in one agent session
   3. **Dependency correctness** — no circular deps, correct sequencing
   4. **File scope safety** — tasks don't modify same files in phases within the same parallel group
   5. **Acceptance criteria completeness** — every task has verifiable criteria (not vague)
   6. **Test coverage mapping** — every behavior has a corresponding test requirement
   7. **Consistency** — no conflicting instructions across phases
   8. **Codebase alignment** — plan respects existing patterns from project overview + component docs
3. **Planning rules** — read all files in `.workflow/rules/planning/` (if any exist)
4. **Component docs** — the `.analysis.md` files used during planning
5. **Source code of relevant files** — for codebase alignment checks (dimension 8), the reviewer may need to compare plan instructions against actual code patterns
6. **Project overview** — `.workflow/project-overview.md`

If review has FAILs: return findings to the planner agent for revision (max 2 revision rounds).

### Step 7: User Review

Present the final plan to the user:
1. Display the plan summary, phase overview, dependency graph, and risk assessment directly from the in-memory plan data (files not written yet).
2. User can: **approve**, **request changes**, or **reject**
3. If changes requested: update plan, re-run automated review (Step 6)
4. If approved: proceed to Phase E

## Phase E: Plan Finalization

### Step 8: Write Plan Files

**If creating multiple plans in one session:** Complete Step 8 fully for each plan before starting Step 8 for the next. Each plan gets its own `$PLAN_DIR`. Do NOT interleave — finish writing + init for plan A, then start plan B.

For each plan:

1. Create directory: `.workflow/plans/{YYMMDD}-{slug}/`
   - `{YYMMDD}` = today's date (e.g., `260326`)
   - `{slug}` = kebab-case from plan name (e.g., `user-export`)
   - **Store this as `$PLAN_DIR`** — all subsequent CLI calls for THIS plan use `--plan-dir $PLAN_DIR`
2. Write `plan.json` with status updated to `"approved"`
3. Write `phase-{N}.json` for each phase
4. **MANDATORY:** Initialize state via CLI (do NOT write state.json manually):
   ```
   python .claude/scripts/workflow_cli.py init $PLAN_DIR
   ```
   This creates `state.json` from `plan.json` + phase files with the correct list-of-objects format.

5. Tell the user: "Plan created at `$PLAN_DIR`. Run `/execute` to start implementation."
6. Display the initial state:
   ```
   python .claude/scripts/workflow_cli.py state show --plan-dir $PLAN_DIR
   ```

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

## Phase G: Template Suggestion

After reflection, assess whether this plan represents a **repeatable pattern**:
- Does this plan create something that will likely be built again with variations? (new provider integration, new CRUD page, new API resource, new module following an existing pattern)
- Are there already similar components in the codebase that followed the same shape?

If yes, suggest to the user: "This plan looks like a repeatable pattern ({reason}). Want to create a template so future instances are faster? I can do it now while the full context is fresh."

If user agrees: use the Skill tool to invoke `/template-create` with `--from-session` flag.

When invoking, pass to the template-extractor agent:
1. **Plan summary** — what was built and why
2. **Component intelligence** — key findings from analysis that shaped the plan
3. **Phase/task structure** — how the work was decomposed
4. **Affected components** — what was touched and their `.analysis.md` docs
5. **Reflection findings** — discoveries and corrections from Phase F
6. **Key decisions and reasoning** — trade-offs made during planning and why

If user declines: fine. They can run `/template-create` later.

## Constraints
- Do NOT include implementation code in the plan — tasks describe WHAT, executor decides HOW
- Do NOT create more than 5 phases unless the feature genuinely requires it
- Do NOT create tasks that require more than one agent session to complete
- Do NOT put tasks that modify the same files in the same parallel group
- Do NOT skip the automated review step
- Do NOT proceed past user review without explicit approval
- Do NOT write state.json manually — always use `workflow_cli.py init`
- Do NOT run CLI commands without `--plan-dir $PLAN_DIR` (when plan files exist on disk)
