# Analyzer Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect all before constructing the prompt.

### Single Component (no recursion)

| Data | Source |
|------|--------|
| Mode | `single` |
| Component source code | All files in the module, or the single entry file |
| Test files | Test files for this component (if they exist) |
| Existing analysis | The existing `.analysis.md` file (if update mode — source changed but doc exists) |
| Project overview | `.workflow/project-overview.md` |
| Output path | Co-located `.analysis.md` path determined in Step 0 |

### Dependency Tree (recursive)

| Data | Source |
|------|--------|
| Mode | `tree` |
| Dependency graph | Built in Step 2a — `{component: [direct_dependencies]}` |
| Analysis order | Topological sort from Step 2b — leaf-to-root sequence |
| All source code | Collected in Step 2c — labeled by component name and file path |
| Test files | Test files for each component (if they exist) |
| Project overview | `.workflow/project-overview.md` |
| Output paths | Co-located `.analysis.md` path for each component in the tree |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions. Include tree-specific sections only for recursive mode. Pass everything below this line as the subagent prompt.

**Mode:** {mode}
`single` = analyze one component. `tree` = analyze multiple components bottom-up.

**Dependency Graph:** *(tree mode only)*
{dependency_graph}
Shows which component depends on which. Format: `A → [B, C]` means A depends on B and C. Use this to understand the relationships BEFORE reading any code.

**Analysis Order:** *(tree mode only)*
{analysis_order}
Analyze components in this exact order (leaf → root). Write each `.analysis.md` to disk before moving to the next. By the time you reach a component, you've already deeply understood all its dependencies.

**Output Paths:** *(tree mode only)*
{output_paths}
Map of component name → `.analysis.md` file path. Write each analysis to its specified path.

**Source Code:**
{source_code}
For single mode: one component's source files.
For tree mode: ALL components' source files, labeled by component name and file path. Read the dependency graph first to understand how they connect, then read code in analysis order.

**Existing Analysis:** *(single mode, update only — omit if writing from scratch)*
{existing_analysis}
The current `.analysis.md` content. Preserve structure and any still-accurate content. Update what changed.

**Test Files:**
{test_files}
Tests reveal intended behavior and edge cases. Use to populate the Tests table and validate your understanding.

**Project Overview:**
{project_overview}
Codebase architecture and conventions. Ensure your analysis fits the project's module structure and naming.

**Output Path:** *(single mode only)*
`{output_path}`
Write the analysis file to this exact path.

## Analysis Instructions

### For single mode
Analyze the component's source code. Write one `.analysis.md` file.

### For tree mode
Follow the analysis order strictly. For each component:

1. **Read** its source code and its direct dependencies' source code (both are in your context)
2. **Understand** how it uses its dependencies — not just the interface calls, but the interaction patterns, edge cases, and assumptions
3. **Write** `{Component}.analysis.md` to the specified output path
4. **Build forward** — your understanding deepens with each component. By the time you reach the root, you understand the entire stack

**Cross-component insights:** When analyzing a component, you may notice behaviors that only matter because of how a dependency works internally. Capture these in the Hidden Details table — they're the most valuable findings.

## Frontmatter Schema

Every `.analysis.md` must include this frontmatter:

```yaml
---
name: {ComponentName}
type: {react-component | service | api-route | hook | utility | module | middleware | model}
summary: "{One-paragraph summary — what it is, what it does, key features}"
source_hash: {sha256-hex-digest-of-entry-files}
last_analyzed: {YYYY-MM-DD}
analysis_version: v2
entry_files: [{relative paths to source files}]
dependency_tree:         # full transitive dependencies — omit if leaf component
  - name: {DepName}
    entry_files: [{relative paths}]
    source_hash: {sha256-hex-digest}
---
```

**Computing `source_hash`:** Use the CLI `hash` command with the component's `entry_files`. For tree mode, compute each component's hash from its own entry files.

**Computing `dependency_tree`:** Include ALL transitive dependencies, not just direct ones. For each, record its `entry_files` and the `source_hash` computed from those files at analysis time.

## Output Format

Write the analysis file using this exact structure. The CONTENT section is read most often by other agents; the EXTRA section only when modifying internals.

```markdown
---
{frontmatter as above}
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
