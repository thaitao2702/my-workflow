# Acceptance Verifier Prompt Template

## For Orchestrator — Data to Collect

Each row names a `{placeholder}` and where to get its value. Collect all before constructing the prompt.

| Placeholder | Source |
|-------------|--------|
| `{mode}` | Resolved from `.workflow/config.json`: if `acceptance_mode` is `auto`, use `test` when `test_command` exists, `reason` otherwise. If `test` or `reason`, use directly. |
| `{acceptance_specs}` | `phase-{N}.json` → `acceptance_specs` |
| `{task_file_lists}` | `phase-{N}.json` → `tasks[].files` (map task-id to file list for traces_to resolution) |
| `{code_changes}` | `git diff` for this phase |
| `{test_command}` | `.workflow/config.json` → `test_command` (test mode only, omit for reason mode) |
| `{test_command_timeout}` | `.workflow/config.json` → `test_command_timeout` (test mode only, default 120000) |
| `{project_overview_path}` | `.workflow/project-overview.md` — pass path only |
| `{component_analysis_paths}` | Paths to relevant `.analysis.md` files |
| `{phase_goal}` | `phase-{N}.json` → `goal` |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions and mode instructions. Pass everything below this line as the subagent prompt.

**Mode:** {mode}
`test` = write and execute acceptance test code. `reason` = read code and reason about whether specs are met. Follow mode-specific instructions below.

**Acceptance Specs:**
{acceptance_specs}
Each spec has: id, description, traces_to (task-ids), verification_type, verify_by. The `verify_by` field is your specification — verify exactly what it says.

**Task File Lists:**
{task_file_lists}
Mapping of task-id to file list. Use `traces_to` in each spec to find which files to examine for that spec.

**Code Changes:**
{code_changes}
The diff for this phase. Use for understanding what was implemented.

**Test Command:** *(test mode only)*
{test_command}
Use this command to run tests. Place acceptance test files following project conventions so the test runner discovers them.

**Test Command Timeout:** *(test mode only)*
{test_command_timeout}
Maximum milliseconds for test execution.

**Context Files (load before verifying):**
Load all these files upfront — issue all Read calls in parallel within a single response.

| Category | Paths |
|----------|-------|
| Project overview | {project_overview_path} |
| Component analysis | {component_analysis_paths} |

After loading, reference from context.

**Phase Goal:**
{phase_goal}
What this phase achieves. Context for understanding the specs.

## Mode-Specific Instructions

### Test Mode

1. For each spec, write a focused acceptance test targeting the `verify_by` scenario.
2. Follow the project's test conventions (framework, file location, naming patterns). Detect these from existing test files and project overview.
3. Run tests using the test command. Test output is your evidence.
4. Do NOT modify production code. Only write test files.
5. If the test infrastructure fails (command not found, dependencies missing), report as `infra_failure` escalation.

### Reason Mode

1. Load all source files for all specs upfront. Collect all file paths from `traces_to` → task file lists across all specs, then issue all Read calls in parallel within a single response.
   Then for each spec, reference the relevant files from the loaded context.
2. Trace the `verify_by` scenario through the code path.
3. Cite specific file:line references for every claim.
4. If a code path is missing, incomplete, or incorrect — that is a FAIL with the gap described.
5. Do NOT write any files. Read and reason only.

## Output Format

Follow this format exactly:

```
## Status
**Result:** PASS | FAIL | PARTIAL
**Mode:** test | reason
**Verified:** {passed}/{total}
**Failed Specs:** [{spec-ids}]

## Specs
### {spec-id}: {description}
**Result:** PASS | FAIL | SKIP
**Evidence:** {test output for test mode | file:line citations for reason mode}
**Gap:** {what's missing or broken} | —

## Escalations
| Type | Spec | Description |
|------|------|-------------|
| ambiguous_spec ∣ infra_failure ∣ untestable | {spec-id} | {details} |
```

- **Status.Result:** `PASS` = all specs pass. `FAIL` = one or more specs fail. `PARTIAL` = some specs verified, others skipped due to escalation.
- **Specs:** One subsection per spec, in order. Every spec must be evaluated — no skipping unless escalated.
- **Evidence:** Specific and concrete. Test mode: test output showing pass/fail. Reason mode: file:line citations showing code path. Never generic ("looks correct").
- **Gap:** Describe what's missing or broken. Use "—" only if PASS.
- **Escalations:** Issues that prevented verification. Write "None" if no issues.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: PASS ∣ FAIL ∣ PARTIAL | Decide: proceed, fix, or escalate |
| | `**Verified**`: passed/total | Quick coverage gauge |
| | `**Failed Specs**`: list of spec-ids | Know which specs need attention |
| `## Specs` | Per spec: `**Result**`, `**Evidence**`, `**Gap**` | Specific failures to fix if FAIL |
| `## Escalations` | Table: Type, Spec, Description | Infrastructure or spec issues to resolve before re-verification. Type enum: `ambiguous_spec`, `infra_failure`, `untestable` |
