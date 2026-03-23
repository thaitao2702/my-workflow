---
description: "Create an execution plan from requirements — phases, tasks, dependency graph, quality review"
---

# /plan — Create Execution Plan

You are creating a detailed, dependency-aware, quality-checked execution plan. Transform requirements into phased tasks that an executor agent can implement.

**Input:** `/plan "requirement text"`, `/plan ./path/to/requirements.md`, `/plan gh:123`, or `/plan jira:PROJ-456`
**Output:** `.workflow/plans/{YYMMDD}-{name}/` directory with `plan.md`, phase files, and `state.md`

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
3. If 2+ keywords match a template:
   - Tell the user: "Found matching template: **{name}** — {description}"
   - Ask: "Use this template as a starting point? (yes/no/show me)"
   - If yes: use the Skill tool to invoke `/template-apply` with the template name. Use its output as the basis for planning.
   - If "show me": display the template overview, then ask again
   - If no: proceed with normal planning

### Step 3: Clarification

Analyze requirements for gaps, ambiguities, and assumptions:

1. Read `.workflow/project-overview.md` for architectural context
2. Check affected components — read their `.analysis.md` frontmatter if they exist
3. Generate specific clarification questions (not open-ended):
   - Missing acceptance criteria?
   - Ambiguous scope boundaries?
   - Assumptions about existing architecture?
   - Missing error handling / edge case specifications?
4. Present questions to user, wait for answers
5. Loop until no more questions (max 3 clarification rounds)

If requirements are clear and complete, skip directly to Phase B.

## Phase B: Component Intelligence Gathering

### Step 4: Analyze Affected Components

From requirements + project overview, identify components that will be:
- **Modified** — existing components that need changes
- **Extended** — components that need new features added
- **Consumed** — components whose API the new code will use
- **Created** — new components (check similar existing ones for patterns)

For each affected component, run staleness check:
1. Check if `{component}.analysis.md` exists alongside the source
2. If exists: read frontmatter, compare `last_commit` vs `git log -1 --format=%H -- {entry_files}`
   - Current → load it (Level 1: frontmatter + CONTENT section)
   - Stale → use the Skill tool to invoke `/analyze` on the component path
3. If doesn't exist → use the Skill tool to invoke `/analyze` on the component path

After this step: all affected components have up-to-date `.analysis.md` files.

**Why before planning:** Planning without component knowledge = planning on assumptions. If a component can't do what the planner assumes, we discover it at execution time — wasted work + expensive replanning. Analyzing first is cheaper than failing mid-execution.

## Phase C: Plan Creation

### Step 5: Spawn Planner Agent

Use the Agent tool to spawn a subagent with `.claude/agents/planner.md`.

Provide the agent with:
1. **Finalized requirements** (from Step 1-3)
2. **Project overview** — `.workflow/project-overview.md`
3. **Component analysis docs** — relevant `.analysis.md` files (Level 1: frontmatter + CONTENT)
4. **Template context** (if `/template-apply` was used in Step 2)
5. **Config** — `.workflow/config.json`

The planner agent returns: `plan.md` content + phase file contents.

### Plan File Format: `plan.md`

```markdown
---
name: {feature-name}
created: {YYYY-MM-DD}
status: draft
total_phases: {N}
total_tasks: {N}
---

## Summary
{What we're building and why — 2-3 sentences}

## Scope
### In Scope
- {requirement 1}

### Out of Scope
- {explicitly excluded item}

## Component Intelligence
{Key findings from pre-planning analysis that shaped this plan}

## Phase Overview
| # | Phase | Tasks | Dependencies | Group |
|---|-------|-------|-------------|-------|
| 1 | ... | N | none | A |
| 2 | ... | N | Phase 1 | B |

## Dependency Graph
```mermaid
graph TD
    ...
```

## Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|-----------|
| ... | ... | ... |
```

### Phase File Format: `phase-NN-{slug}.md`

```markdown
---
phase: {number}
name: {phase-name}
status: pending
group: {A/B/C}
depends_on: [{phase numbers}]
affected_components: [{component paths}]
---

## Goal
{What this phase achieves}

## Tasks
### Task 1: {task-name}
- **Description:** {what to do}
- **Files:** {files to create/modify}
- **Acceptance Criteria:**
  - {verifiable criterion}
- **Test Requirements:**
  - {test to write}

## Phase Completion Checklist
- [ ] All tasks completed
- [ ] All tests pass
- [ ] Code review passed
- [ ] Affected component docs updated
```

## Phase D: Plan Review

### Step 6: Automated Review

Use the Agent tool to spawn a subagent with `.claude/agents/reviewer.md`.

Provide the agent with:
1. **The plan** (`plan.md` + all phase files)
2. **Planning rules** — read all files in `.workflow/rules/planning/` (if any exist)
3. **Component docs** — the `.analysis.md` files used during planning
4. **Project overview** — `.workflow/project-overview.md`

The reviewer checks **8 dimensions:**
1. **Requirement coverage** — every requirement maps to at least one task
2. **Task atomicity** — each task is completable in one agent session
3. **Dependency correctness** — no circular deps, correct sequencing
4. **File scope** — tasks don't modify same files in parallel phases
5. **Acceptance criteria completeness** — every task has verifiable criteria
6. **Test coverage mapping** — every behavior has a corresponding test requirement
7. **Consistency** — no conflicting instructions across phases
8. **Codebase alignment** — plan respects existing patterns from project overview + component docs

If review has FAILs: return findings to the planner agent for revision (max 2 revision rounds).

### Step 7: User Review

Present the final plan to the user:
1. Show: phase summary, dependency graph, parallel groups, risk assessment
2. User can: **approve**, **request changes**, or **reject**
3. If changes requested: update plan, re-run automated review (Step 6)
4. If approved: proceed to Phase E

## Phase E: Plan Finalization

### Step 8: Write Plan Files

1. Create directory: `.workflow/plans/{YYMMDD}-{slug}/`
   - `{YYMMDD}` = today's date (e.g., `260322`)
   - `{slug}` = kebab-case from plan name (e.g., `user-export`)
2. Write `plan.md` with status updated to `approved`
3. Write `phase-NN-{slug}.md` for each phase
4. Write `state.md` with initial state (all phases pending, all tasks unchecked)

### State File Format: `state.md`

```markdown
---
plan: {plan-name}
status: approved
current_phase: 1
current_task: task-01
last_updated: {ISO datetime}
started: {ISO datetime}
---

## Execution Progress

### Phase 1: {phase-name} [PENDING]
- [ ] task-01: {task description}
- [ ] task-02: {task description}

### Phase 2: {phase-name} [PENDING]
- [ ] task-01: {task description}

## Session Log
```

5. Tell the user: "Plan created at `.workflow/plans/{dir}/`. Run `/execute` to start implementation."

## Constraints
- Do NOT include implementation code in the plan — tasks describe WHAT, executor decides HOW
- Do NOT create more than 5 phases unless the feature genuinely requires it
- Do NOT create tasks that require more than one agent session to complete
- Do NOT put tasks that modify the same files in the same parallel group
- Do NOT skip the automated review step
- Do NOT proceed past user review without explicit approval
