# Analyzer Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect all before constructing the prompt.
Which rows to include depends on the mode (full vs update).

### Full Mode

| Data | Source |
|------|--------|
| Mode | `full` |
| Component source code | All files in the module, or the single entry file |
| Test files | Test files for this component (if they exist) |
| Dependency analysis docs | Dependency `.analysis.md` files (frontmatter + CONTENT only) — read fresh from disk, just written/confirmed in Step 2 |
| Project overview | `.workflow/project-overview.md` |
| Output path | Co-located `.analysis.md` path determined in Step 0 |

### Update Mode

| Data | Source |
|------|--------|
| Mode | `update` |
| Existing analysis | The existing `.analysis.md` file (full content) |
| Git diff | `git diff {last_commit}..HEAD -- {entry_files}` |
| Current source code | All entry files |
| Dependency analysis docs | Dependency `.analysis.md` files (frontmatter + CONTENT only) — read fresh from disk |
| Project overview | `.workflow/project-overview.md` |
| Output path | Same file location (overwrite) |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions. Pass everything below this line as the subagent prompt.

**Mode:** {mode}
Whether to write from scratch (full) or update an existing analysis (update).

**Component Source Code:**
{component_source_code}
The code to analyze. Read carefully — every public API, hidden behavior, and integration pattern comes from here.

**Existing Analysis:** *(update mode only)*
{existing_analysis}
The current analysis doc. Preserve structure and any still-accurate content. Update what the diff changed.

**Git Diff:** *(update mode only)*
{git_diff}
What changed since last analysis. Focus your updates on sections affected by these changes.

**Test Files:**
{test_files}
Tests reveal intended behavior and edge cases. Use to populate the Tests table and validate your understanding.

**Dependency Analysis Docs:**
{dependency_analysis_docs}
Analysis of components this one depends on. Use their Public API tables to understand the contracts this component relies on.

**Project Overview:**
{project_overview}
Codebase architecture and conventions. Ensure your analysis fits the project's module structure and naming.

**Output Path:** `{output_path}`
Write the analysis file to this exact path.

**Output Format:**
Write the analysis file using this exact structure. The CONTENT section is read most often by other agents; the EXTRA section only when modifying internals.

```markdown
---
name: {ComponentName}
type: {react-component | service | api-route | hook | utility | module | middleware | model}
summary: "{One-paragraph summary — what it is, what it does, key features}"
last_analyzed: {YYYY-MM-DD}
last_commit: {git-hash}
analysis_version: v1
dependencies: [{local dependency names}]
entry_files: [{relative paths to source files}]
---

<!-- PART:CONTENT_START -->

## Purpose & Use Cases
{Complete description — all major features, usage scenarios, why it exists}

## Dependencies
| Dependency | Type | Purpose | Key Interface |
|-----------|------|---------|--------------|

## Public API / Props
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|

## Integration Patterns
{Real code examples showing how to USE this component — 2-3 scenarios}

## Architecture Diagram
```mermaid
graph TD
    ...
```

## Data Flow
```mermaid
graph LR
    ...
```

## Entrypoints & Files
| File | Role |
|------|------|

## Patterns Used
{Named patterns with brief explanations}

## Hidden Details & Non-obvious Behaviors
| What | Why | Risk | Test Suggestion |
|------|-----|------|----------------|

<!-- PART:CONTENT_END -->

<!-- PART:EXTRA_START -->

## Tests
| Test File | Coverage |
|-----------|----------|

## Performance Notes
{Caching, rendering optimizations, known bottlenecks}

<!-- PART:EXTRA_END -->
```
