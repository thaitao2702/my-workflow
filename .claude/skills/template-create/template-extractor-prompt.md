# Template Extractor Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Data varies by source mode — collect what applies.

### All Modes

| Placeholder | Source |
|-------------|--------|
| `{template_name}` | User input or calling skill suggestion |
| `{project_overview_path}` | `.workflow/project-overview.md` — pass path only |
| `{analysis_doc_paths}` | Paths to `.analysis.md` files for touched components (if they exist) |


### Mode: A-session (from current session — richest)

| Data | Source |
|------|--------|
| Plan summary | In-session plan context — what was built and why |
| Phase/task structure | In-session — how the work was decomposed |
| Component intelligence | In-session — analysis findings that shaped the plan |
| Execution discoveries | In-session — wrong assumptions, hidden behaviors found during implementation |
| Key decisions | In-session — trade-offs, reasoning, adaptations during planning or execution |
| Git diff | `git diff {execution_start_commit}..HEAD` |

### Mode: A-disk (from completed plan)

| Data | Source |
|------|--------|
| Plan summary + phases + component intelligence | CLI: `plan review-dump --plan-dir $PLAN_DIR` — returns all plan data in one call |
| Git diff | `git diff {execution_start_commit}..HEAD` |

### Mode: B (from git history)

| Data | Source |
|------|--------|
| Git diff | `git diff` for specified range or branch |
| Git log | `git log` for the range (commit messages provide intent) |

### Mode: C (from existing code)

| Data | Source |
|------|--------|
| Source files | Current content of specified files |

### Mode: D (manual description)

| Data | Source |
|------|--------|
| User description | Verbal description of the pattern |
| Supporting files | Any files the user references |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Include only sections that have data. Keep purpose descriptions. Pass everything below this line as the subagent prompt.

**Template Name:** {template_name}
The name for this template. Use it in your output headings and variable naming.

**Source Material:**
{source_material}
The concrete implementation to abstract from. This is your primary input — read it carefully before imagining variant cases.

**Session Context:** *(include only for A-session mode)*
{session_context}
Reasoning, decisions, and discoveries from the planning/execution session. This is context that doesn't survive in files — trade-offs considered, assumptions corrected, adaptations made. Use it to produce richer gotchas and more accurate variability classifications.

**Context Files (load before extracting):**
Load all these files upfront — issue all Read calls in parallel within a single response.

| Category | Paths |
|----------|-------|
| Analysis docs | {analysis_doc_paths} |
| Project overview | {project_overview_path} |

After loading, reference from context.

**Your Task:**

Apply multi-case reasoning (see your agent instructions) to extract the repeatable pattern. Produce your output following the format below — full detail, not a summary. The orchestrator will present a condensed summary to the user first for direction validation, then show the full output for final review. All refinement after your output is handled by the orchestrator with the user.

## Output Format

Follow this format exactly:

```
## Status
**Result:** SUCCESS | FAILURE
**Pattern:** {one-line description of the extracted pattern}
**Steps:** {N}
**Variables:** {N}
**Imagined Cases:** [{2-3 case descriptions used for multi-case reasoning}]

## Template Content
{complete template.md — YAML frontmatter + full body, as raw markdown}

## Reference Files
### references/{slug_1}.md
{complete annotated content with [F]/[P]/[G] markers}

### references/{slug_2}.md
{complete annotated content with [F]/[P]/[G] markers}

## Escalations
| Step | Uncertainty | Current Classification | Notes |
|------|-----------|----------------------|-------|
| {step name} | {what's uncertain} | F ∣ P ∣ G | {why flagged for user review} |
```

- **Status.Result:** `SUCCESS` = pattern extracted successfully. `FAILURE` = source material insufficient to extract a meaningful pattern.
- **Template Content:** The complete `template.md` file content — frontmatter with name, description, trigger_keywords, variables, followed by full body with Overview, Variables table, Steps with [F]/[P]/[G], Integration Points, Tests, Gotchas.
- **Reference Files:** One `###` subsection per reference file. Filename must match the references in Template Content steps.
- **Escalations:** Steps where the variability classification is uncertain. Write "None" if all classifications are confident.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: SUCCESS ∣ FAILURE | Verify extraction completed |
| | `**Pattern**`: one-line description | Present in direction review summary |
| | `**Steps**`, `**Variables**` | Summary counts for direction review |
| | `**Imagined Cases**` | Verify multi-case reasoning was applied |
| `## Template Content` | Raw markdown block | Save to `.workflow/templates/{name}/template.md` after user review |
| `## Reference Files` | Subsections by `### references/{slug}.md` | Save each to `.workflow/templates/{name}/references/{slug}.md` |
| `## Escalations` | Table: Step, Uncertainty, Current Classification, Notes | Present to user during direction review for confirmation |
