# Plan Reviewer Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect all before constructing the prompt.

| Data | Source |
|------|--------|
| `$PLAN_DIR` | Resolved in Step 7 |
| Plan JSON | CLI: read full plan (see reference doc) |
| Phase JSONs | CLI: read each phase (see reference doc) |
| Planning rules | `.workflow/rules/planning/*.md` (if any exist) |
| Component docs | `.analysis.md` files used during planning |
| Source code | Relevant source files for codebase alignment checks |
| Project overview | `.workflow/project-overview.md` |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions and review dimensions. Pass everything below this line as the subagent prompt.

**Plan Directory:** `{$PLAN_DIR}`
Use the CLI to read plan and phase data. See `.claude/scripts/workflow_cli.reference.md` for commands.

**Planning Rules:**
{planning_rules}
Project-specific planning standards. Flag violations.

**Component Docs:**
{component_docs}
Analysis artifacts from planning. Verify the plan respects these contracts and hidden behaviors.

**Source Code:**
{source_code}
Relevant source files. Use for codebase alignment checks (dimension 10).

**Project Overview:**
{project_overview}
Codebase architecture, modules, and conventions. Verify the plan fits existing patterns.

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

- **Status.Result:** `PASS` = all 10 dimensions pass. `FAIL` = one or more dimensions fail.
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
