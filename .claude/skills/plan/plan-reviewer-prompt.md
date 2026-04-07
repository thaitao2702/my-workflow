# Plan Reviewer Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect paths only — the subagent reads content itself.

| Data | Source |
|------|--------|
| `$PLAN_DIR` | Resolved in Step 7 |
| Planning rules dir | `.workflow/rules/planning/` — pass directory path, or `None` if it doesn't exist |
| Component doc paths | Paths of `.analysis.md` files used during planning (from Step 4b) |
| Source file paths | Paths of relevant source files for codebase alignment (from Step 4a) |
| Project overview path | `.workflow/project-overview.md` |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected paths. Keep purpose descriptions and review dimensions. Pass everything below this line as the subagent prompt.

**Plan Directory:** `{$PLAN_DIR}`
Read plan and phase data using the CLI. See `.claude/scripts/workflow_cli.reference.md` for commands.
- Full plan: `plan get --plan-dir {$PLAN_DIR}`
- Phase list: `plan phases --plan-dir {$PLAN_DIR}`
- Phase detail: `phase show N --plan-dir {$PLAN_DIR}` for each phase

**Planning Rules Directory:** `{planning_rules_dir}`
Read all `.md` files in this directory. These are project-specific planning standards — flag violations.
If `None` or directory does not exist: no project-specific planning rules to enforce.

**Component Docs:**
{component_doc_paths}
Read each file listed above. These are analysis artifacts from planning — verify the plan respects their contracts and hidden behaviors.
If `None`: no component analysis available — note in evidence for analysis-dependent checks.

**Source Files:**
{source_file_paths}
Read each file listed above. Use for codebase alignment checks (dimension 10).
If `None`: skip codebase alignment verification, mark as PASS with evidence "no source files provided for verification."

**Project Overview:** `{project_overview_path}`
Read this file. Codebase architecture, modules, and conventions — verify the plan fits existing patterns.

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
