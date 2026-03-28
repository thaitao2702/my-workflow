# Template Extractor Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Data varies by source mode — collect what applies.

### All Modes

| Data | Source |
|------|--------|
| Template name | User input or calling skill suggestion |
| Project overview | `.workflow/project-overview.md` |
| Analysis docs | `.analysis.md` files for touched components (if they exist) |

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
| Plan summary | CLI: read plan summary (see reference doc) |
| Phase/task structure | CLI: read each phase's tasks (see reference doc) |
| Component intelligence | CLI: read plan component_intelligence field |
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

**Template Name:** `{template_name}`
The name for this template. Use it in your output headings and variable naming.

**Source Material:**
{source_material}
The concrete implementation to abstract from. This is your primary input — read it carefully before imagining variant cases.

**Session Context:** *(include only for A-session mode)*
{session_context}
Reasoning, decisions, and discoveries from the planning/execution session. This is context that doesn't survive in files — trade-offs considered, assumptions corrected, adaptations made. Use it to produce richer gotchas and more accurate variability classifications.

**Analysis Docs:**
{analysis_docs}
Structured component knowledge. Use to understand integration patterns and hidden behaviors that should carry into the template.

**Project Overview:**
{project_overview}
Codebase architecture and conventions. Use to ensure the template fits the project's patterns.

**Your Task:**

Apply multi-case reasoning (see your agent instructions) to extract the repeatable pattern. Produce:

1. **Template overview** — one-line description of the pattern and when to use it
2. **Steps** — ordered sequence with `[F]`/`[P]`/`[G]` classification per step
3. **Variables** — names, descriptions, example values from the original
4. **Integration points** — where new code connects to existing code, with variability level
5. **Test patterns** — what tests follow the pattern
6. **Gotchas** — non-obvious things learned, noting which are pattern-level vs instance-specific
7. **Reference file contents** — annotated snapshots of key source files with `[F]`/`[P]`/`[G]` markers

Return the complete `template.md` content and reference file contents. The orchestrator will present your output to the user for review before writing to disk.
