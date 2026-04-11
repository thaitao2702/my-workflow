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

Evaluate against all 13 dimensions:

1. **Requirement coverage** — every requirement maps to at least one task
2. **Task atomicity** — each task is completable within its phase's agent session
3. **Task granularity** — tasks are coherent units of work. Flag: trivially small standalone tasks (1-3 line changes), tightly coupled changes split across tasks, phases with too many tasks to complete in one agent session
4. **Task description quality** — descriptions say WHAT/WHY, not HOW for internal implementation. Flag: private implementation details (polling intervals, internal method bodies, algorithm choices, line numbers). Do NOT flag references to interface contracts declared in `interface_contracts[]` — these are cross-phase dependency coordination, not implementation leakage. Flag descriptions that define signatures inline instead of referencing the contract by phase and ID.
5. **Dependency correctness** — no circular deps, correct sequencing
6. **File scope safety** — tasks don't modify same files in phases within the same parallel group
7. **Acceptance criteria validity** — every task has verifiable criteria (not vague), AND every criterion passes the generation constraint litmus tests. Flag: compiler/language guarantees tested as criteria, criteria dependent on future tasks, tautologies (restate task description as verification), structural-not-behavioral checks, subjective terms without thresholds, contradictions within a task's criteria set. Example violations: "Verify abstract class can't be instantiated" (compiler guarantee), "Verify enum has specified values" (tautology — true by definition once written)
8. **Test requirement validity** — every behavior has a corresponding test requirement, AND every requirement passes the generation constraint litmus tests. Flag: language/compiler/framework behavior tested instead of task code, cross-task scope leaks (testing artifacts from a different task), unfalsifiable tests (any compiling implementation passes), zero-logic artifact testing (interfaces, enums, type aliases, static config), vague predicates ("works correctly"), implementation prescription ("uses Singleton pattern"), redundancy (two requirements test same behavior). Example violations: "Verify concrete subclass implements all abstract methods" (scope leak — subclass is another task), "Verify interface defines correct properties" (zero-logic — interfaces have no runtime behavior)
9. **Consistency** — no conflicting instructions across phases
10. **Codebase alignment** — plan respects existing patterns from project overview + component docs
11. **Acceptance spec coverage** — every requirement in scope.in_scope traces to at least one acceptance_spec across all phases, every spec has a concrete verify_by that enables unambiguous PASS/FAIL, verify_by scenarios are framework-agnostic, and traces_to references valid task-ids
12. **System composition** — trace the end-to-end data/control flow through the plan as a whole. Every plan describes a system, not just a collection of tasks. Flag: integration gaps where Phase A produces an artifact Phase B consumes but no task wires them together, missing infrastructure tasks the system needs but no requirement states (adapters, middleware, config, migrations, API wiring), cross-phase assumptions that are individually valid but incompatible when composed (e.g., Phase 1 creates a model shape that Phase 3's query patterns can't efficiently use), end-to-end user flows that fall through a crack between task boundaries. Example violation: three tasks create a CSV serializer, a permission gate, and a streaming paginator — but no task creates the endpoint that composes all three into a working export feature
13. **Interface dependency coverage** — when Phase X's task describes calling, receiving, or importing code from Phase Y, verify: (a) the defining phase (Y) has an `interface_contracts` entry for that service, (b) the consuming phase (X) task description references the contract by phase and ID, (c) the contract includes: ID, expected class/module name, description, defined_in_task, and consumed_by_phases, (d) consumed_by_phases matches the actual consuming phases found in task descriptions, (e) **sequential ordering:** the defining phase is in an earlier execution group than every phase in consumed_by_phases — phases with interface dependencies MUST NOT be in the same parallel group. Flag: cross-phase code dependencies with no contract declared. Flag: "calls the helper" or "receives via injection" without referencing a specific contract by phase and ID. Flag: producing and consuming phases in the same parallel group.

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

- **Status.Result:** `PASS` = all 13 dimensions pass. `FAIL` = one or more dimensions fail.
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
