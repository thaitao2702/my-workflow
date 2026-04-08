# Plan Reviewer Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect paths only — the subagent reads content itself.

| Placeholder | Source |
|-------------|--------|
| `{$PLAN_DIR}` | Resolved in Step 7 |
| `{planning_rules_dir}` | `.workflow/rules/planning/` — pass directory path, or `None` if it doesn't exist |
| `{component_doc_paths}` | Paths of `.analysis.md` files used during planning (from Step 4b) |
| `{source_file_paths}` | Paths of relevant source files for codebase alignment (from Step 4a) |
| `{project_overview_path}` | `.workflow/project-overview.md` |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected paths. Keep purpose descriptions and review dimensions. Pass everything below this line as the subagent prompt.

**Plan Directory:** {$PLAN_DIR}

**Step 1: Load plan data.**

Run the review-dump command to get all plan data, cross-reference tables, and planning rules:
```
python .claude/scripts/workflow_cli.py plan review-dump --plan-dir {$PLAN_DIR}
```
This returns: plan overview, all phases with tasks and acceptance specs, file ownership by parallel group, requirement trace map, and acceptance spec trace map.

**Step 2: Load context files.**

| Category | Paths | Purpose |
|----------|-------|---------|
| Component docs | {component_doc_paths} | Analysis artifacts — verify the plan respects their contracts and hidden behaviors. `None` = no component analysis available, note in evidence. |
| Source files | {source_file_paths} | For codebase alignment checks (dimension 10). `None` = skip codebase alignment, mark as PASS. |
| Project overview | {project_overview_path} | Codebase architecture and conventions. |
| Planning rules | {planning_rules_dir} | Read all `.md` files in this directory. Project-specific planning standards — flag violations. `None` or missing = no rules to enforce. |

Load all files listed above upfront before evaluating any dimension.

**Step 3: Evaluate dimensions using loaded context.**
Only make additional reads if you discover during evaluation that you need a file not loaded in step 2.

**Step 4: For codebase alignment (dimension 10), grep if needed.**
If the plan references specific classes, functions, or patterns that should exist in the codebase, verify them. Issue all Grep calls in parallel within a single response.

## Review Dimensions

Evaluate against all 10 dimensions:

1. **Requirement coverage** — every requirement maps to at least one task
2. **Task atomicity** — each task is completable within its phase's agent session
3. **Task granularity** — tasks are coherent units of work. Flag: trivially small standalone tasks (1-3 line changes), tightly coupled changes split across tasks, phases with too many tasks to complete in one agent session
4. **Task description quality** — descriptions say WHAT/WHY, not HOW. Flag: exact property paths, method signatures, implementation code, line numbers in descriptions (these belong in analysis docs and source code)
5. **Dependency correctness** — no circular deps, correct sequencing
6. **File scope safety** — tasks don't modify same files in phases within the same parallel group
7. **Acceptance criteria completeness** — every task has verifiable criteria (not vague)
8. **Test coverage mapping** — every behavior has a corresponding test requirement
9. **Consistency** — no conflicting instructions across phases
10. **Codebase alignment** — plan respects existing patterns from project overview + component docs
11. **Acceptance spec coverage** — every requirement in scope.in_scope traces to at least one acceptance_spec across all phases, every spec has a concrete verify_by that enables unambiguous PASS/FAIL, verify_by scenarios are framework-agnostic, and traces_to references valid task-ids

## Output Format

Follow this format exactly:

```
## Status
**Result:** PASS | FAIL
**Passed:** {N}/{total}
**Failed Dimensions:** [{dimension names}]

## Dimensions
### {N}. {Dimension Name}
**Result:** PASS | FAIL
**Evidence:** {specific reference to plan/phase/task}
**Fix Required:** {description of what needs fixing} | —

## Escalations
| Type | Dimension | Description |
|------|-----------|-------------|
| ambiguous_criteria ∣ conflicting_rules ∣ unclassifiable | {dimension name} | {details} |
```

- **Status.Result:** `PASS` = all 11 dimensions pass. `FAIL` = one or more dimensions fail.
- **Dimensions:** One subsection per dimension, in order. Every dimension must be evaluated — no skipping.
- **Fix Required:** Describe what needs fixing. Use "—" only if PASS.
- **Escalations:** Issues with the review criteria themselves, not with the plan. Write "None" if no criteria issues.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: PASS ∣ FAIL | Decide: approve or revise plan |
| | `**Passed**`: N/total | Quick severity gauge |
| | `**Failed Dimensions**`: list of names | Know which dimensions need revision |
| `## Dimensions` | Per dimension: `**Result**`, `**Evidence**`, `**Fix Required**` | Specific plan revisions to apply if FAIL |
| `## Escalations` | Table: Type, Dimension, Description | Criteria issues to resolve before re-review. Type enum: `ambiguous_criteria`, `conflicting_rules`, `unclassifiable` |
