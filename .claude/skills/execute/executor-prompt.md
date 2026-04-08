# Executor Prompt Template

## For Orchestrator — Data to Collect

Each row names a `{placeholder}` and where to get its value. Collect all before constructing the prompt.

| Placeholder | Source |
|-------------|--------|
| `{$PLAN_DIR}` | Resolved in Step 1a |
| `{phase_number}` | Current phase index |
| `{mission_briefing}` | `plan.json` → `summary` |
| `{component_intelligence}` | `plan.json` → `component_intelligence` |
| `{risks}` | `plan.json` → `risks` |
| `{phase_goal}` | `phase-{N}.json` → `goal` |
| `{tasks}` | `phase-{N}.json` → `tasks` (descriptions, acceptance criteria, test requirements, file lists) |
| `{resume_point}` | `state current` output — omit section if starting fresh |
| `{project_overview_path}` | `.workflow/project-overview.md` — pass path only |
| `{component_analysis_paths}` | Paths to relevant `.analysis.md` files — guaranteed fresh by Step 2a analysis gate |
| `{code_quality_rule_paths}` | Paths to `.workflow/rules/code/*.md` files (if any) + `.claude/rules/quality-criteria.md` |
| `{tdd_policy_path}` | `.claude/rules/tdd-policy.md` — pass path only |
| `{user_directives}` | Active user directives from checkpoint fields. Bulleted list. Omit section if none. |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions. Pass everything below this line as the subagent prompt.

**Plan Directory:** {$PLAN_DIR}
Use for all CLI state-tracking calls (`state set-active`, `complete-task`, etc.).

**Phase:** {phase_number}

**Mission Briefing:**
{mission_briefing}
Big-picture context — what we're building, why, and key constraints. Use this to guide implementation decisions when tasks are ambiguous.

**Component Intelligence:**
{component_intelligence}
Hidden constraints and non-obvious behaviors discovered during planning. Violations cause subtle bugs — respect these over your own assumptions.

**Risks & Mitigations:**
{risks}
Handle proactively. When you encounter a listed risk, apply its planned mitigation.

**Phase Goal:**
{phase_goal}
What this phase achieves and how it connects to other phases. Stay within this scope.

**Tasks:**
{tasks}
Implement in order. Each task's acceptance criteria are your definition of done, not suggestions.

**Resume Point:** *(include only if resuming)*
{resume_point}
Skip completed tasks. Start from the first incomplete task.

**Context Files (load before starting):**
Load all these files upfront — issue all Read calls in parallel within a single response, or use the CLI `batch` command.

| Category | Paths |
|----------|-------|
| Project overview | {project_overview_path} |
| Component analysis | {component_analysis_paths} |
| Code quality rules | {code_quality_rule_paths} |
| TDD policy | {tdd_policy_path} |

After loading, reference from context. Only make additional reads for files discovered during implementation.

**User Directives:** *(include only if directives exist)*
{user_directives}
Instructions from the user during this execution. These override default assumptions where applicable.

## Output Format

**CRITICAL:** The main session only receives your final text output — it does NOT see your tool calls, file reads, or reasoning. Everything the orchestrator needs must be in this report. Follow this format exactly.

```
## Status
**Result:** SUCCESS | PARTIAL | FAILURE
**Phase:** {N}
**Tasks Completed:** [{task-ids}]
**Tasks Remaining:** [{task-ids}]

## Result
**Files Changed:** [{paths}]
**Tests Written:** {N}
**Tests Passing:** {N}

## Decisions
| Task | Component | Decision | Reasoning | Alternatives |
|------|-----------|----------|-----------|--------------|
| {task-id} | {path} | {what was decided} | {why} | {what else was considered} |

Only report decisions where the reasoning is NOT self-evident from the code. If someone reading the code would naturally ask "why was it done this way instead of the obvious alternative?", that's a decision worth reporting.

## Discoveries
| Component | What | Why | Risk | Test Suggestion | Category |
|-----------|------|-----|------|-----------------|----------|
| {path} | {what happened} | {why it happens} | {what could go wrong} | {how to test for it} | hidden_behavior ∣ wrong_assumption ∣ edge_case ∣ integration_gotcha |

Only report non-obvious findings — behaviors where someone reading the public API alone would not expect the behavior. Do not report standard patterns, self-evident code, or trivial implementation details. A good test: "Would a developer modifying this component be surprised by this behavior?"

## Escalations
| Type | Task | Description |
|------|------|-------------|
| blocker ∣ ambiguity ∣ scope_mismatch | {task-id} | {details} |
```

- **Status.Result:** `SUCCESS` = all tasks done. `PARTIAL` = some tasks done, stopped due to blocker. `FAILURE` = no tasks completed.
- **Decisions:** One row per non-trivial implementation decision. Skip the table if all decisions were obvious.
- **Discoveries:** One row per unexpected finding. Write "None" if nothing unexpected.
- **Escalations:** One row per issue requiring orchestrator action. Write "None" if no blockers.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: SUCCESS ∣ PARTIAL ∣ FAILURE | Fast triage — proceed, handle partial, or recover |
| | `**Tasks Completed**`: list of task-ids | State verification against CLI |
| | `**Tasks Remaining**`: list of task-ids | Know what's left if PARTIAL |
| `## Result` | `**Files Changed**`, `**Tests Written**`, `**Tests Passing**` | Phase review input, regression check |
| `## Decisions` | Table: Task, Decision, Reasoning | Context for reviewer, inform doc-update |
| `## Discoveries` | Table: Component, What, Why, Risk, Test Suggestion, Category | Persist via CLI `state add-discovery`. Category enum: `hidden_behavior`, `wrong_assumption`, `edge_case`, `integration_gotcha` |
| `## Decisions` | Table: Task, Component, Decision, Reasoning, Alternatives | Persist via CLI `state add-decision`. Only non-obvious decisions where code doesn't explain the rationale. |
| `## Escalations` | Table: Type, Task, Description | Handle before proceeding. Type enum: `blocker`, `ambiguity`, `scope_mismatch` |
