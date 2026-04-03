---
description: |
  Deep-analyze a component — capture hidden knowledge, business logic,
  integration patterns, and non-obvious behaviors. Produces co-located
  `.analysis.md` documentation that planners, executors, and doc-updaters
  consume as component intelligence.

  Use when the user asks to analyze a component, understand how something
  works, document a module, build component knowledge, or says "what does
  this do?" about source code — even if they don't say "analyze." Also
  triggers for dependency tree analysis, component documentation refresh,
  and staleness checks on existing analysis docs.

  Supports single-component and recursive (full dependency tree) modes.

  Do NOT use for code review (use code review skill), plan creation
  (use /plan), or documentation updates after code changes (use /doc-update).
---

# /analyze — Component Analysis

Deep, narrow analysis of a specific component. Produces co-located `.analysis.md` documentation that any AI agent can consume as component intelligence.

**Input:** `/analyze {component-path}` or `/analyze {component-path} --recursive`
**Output:** `{ComponentName}.analysis.md` co-located alongside the source file(s)

---

## Expert Vocabulary Payload

**Component Analysis:** source hash verification, hash-based staleness detection, co-located documentation, component knowledge layer, progressive loading levels (Level 0: frontmatter / Level 1: CONTENT / Level 2: full), CONTENT/EXTRA section partitioning
**Dependency Resolution:** dependency tree construction, topological sort (leaf-to-root), transitive dependency crawl, local vs external classification, path alias resolution (tsconfig `paths`, vite `resolve.alias`, webpack `resolve.alias`), alias map construction
**Analysis Artifacts:** `.analysis.md` schema, YAML frontmatter (source_hash, entry_files, last_analyzed, dependency_tree, analysis_version), Hidden Details table, Integration Patterns section, Architecture/Data Flow diagrams (Mermaid)
**Orchestration:** prompt template filling (agent I/O contract), output envelope parsing, size guard (context window management), verification checklist, bottom-up analysis order

---

## Anti-Pattern Watchlist

### 1. Stale Analysis Accepted
**Detection:** Proceeding with an existing analysis doc without running `analysis check`. Orchestrator skips the staleness check "because the file exists."
**Resolution:** Always run the CLI `analysis check` command before deciding mode. Fresh → stop. Stale → re-analyze. The hash check is the single source of truth for freshness.

### 2. Alias Misclassification
**Detection:** Aliased imports (`@/services/auth`, `~/utils/format`, `#/lib/db`) classified as external packages. Dependency tree is missing local components that are imported via aliases.
**Resolution:** Resolve import aliases BEFORE classifying dependencies. Check `tsconfig.json` paths, `vite.config.*` resolve.alias, `webpack.config.*` resolve.alias, `package.json` imports. Every aliased import that resolves to a project path is a local dependency.

### 3. Out-of-Order Analysis (MAST FM-3.2 variant)
**Detection:** In recursive mode, components analyzed before their dependencies. The topological sort was skipped or ignored. Dependent component's analysis references dependency behaviors without having analyzed the dependency first.
**Resolution:** Enforce leaf-to-root topological order strictly. The analysis order must be computed via topological sort and followed exactly. This ensures the analyzer understands dependencies before dependents.

### 4. Context Overflow Without Guard
**Detection:** Large dependency trees (>8000 lines, ~60K tokens) passed to the analyzer without warning the user. Analyzer output quality degrades silently due to context saturation.
**Resolution:** Compute total source lines before spawning the analyzer. IF exceeds ~8000 lines: warn the user with exact counts and offer to split into subtree analyses. Do not silently proceed with a tree that will strain context.

### 5. Unverified Output
**Detection:** Analyzer results accepted without checking that `.analysis.md` files were actually written, or that frontmatter fields (`source_hash`, `entry_files`, `name`, `type`, `summary`) are populated. Missing files or empty fields go unnoticed.
**Resolution:** After the analyzer completes, verify every expected `.analysis.md` exists at the correct path. Read frontmatter and confirm all required fields are populated. For recursive mode, also verify `dependency_tree` entries. Report any failures.

### 6. Source Re-Reading
**Detection:** Source files read during dependency resolution in Step 2 are read again when constructing the analyzer prompt. The same content is loaded into context twice, wasting attention budget.
**Resolution:** Source code collected during dependency resolution is already in context. Label it by component name and file path and pass it directly to the prompt template. Do NOT re-read files you already have.

### 7. Recursive Mode on Single File
**Detection:** `--recursive` flag used on a leaf component with no local dependencies. Runs the full dependency resolution machinery for a single file that has no dependency tree.
**Resolution:** After building the dependency graph, IF the graph contains only the root with zero local dependencies: fall back to single-component mode automatically. Inform the user: "No local dependencies found — analyzing as single component."

---

## Behavioral Instructions

### Step 1: Parse Input

1. Extract the component path from the user's input.
2. Check for `--recursive` flag.
3. Resolve the path:
   IF path points to a file → single-file component. Output path: `{FileName}.analysis.md` next to the file.
   IF path points to a directory → multi-file module. Output path: `{module-name}.analysis.md` at the module root.

### Step 2: Staleness Check

4. Check if `{component}.analysis.md` already exists at the resolved output path.

   IF no analysis doc exists → proceed to Step 3 (alias resolution).

   IF analysis doc exists → run CLI `analysis check` command (add `--recursive` if recursive mode):
   - `fresh` → report "Analysis is up to date for {component}" and STOP. Do not re-analyze.
   - `stale` → note the reason and which files/deps changed. Proceed to Step 3.
   - `missing` → treat as full mode. Proceed to Step 3.

### Step 3: Resolve Import Aliases

5. Before mapping dependencies, resolve path aliases used in the project.
   Check for alias definitions in: `tsconfig.json` (`paths`), `vite.config.*` (`resolve.alias`), `webpack.config.*` (`resolve.alias`), `package.json` (`imports`), `pyproject.toml` (tool-specific), `.eslintrc` (`import/resolver`).
   Build an alias map (e.g., `@/ → src/`, `~/ → src/`, `#/ → lib/`).
   WHY: aliased imports look like external packages but are local code. Missing them means missing dependency information.

   IF not recursive AND no dependency resolution needed: this alias map is still useful for the analyzer to classify imports correctly — include it in the prompt context.

### Step 4: Dependency Resolution (recursive mode only)

6. IF `--recursive` flag is NOT present: skip to Step 5.

7. Build the dependency tree:
   a. Read the component's source files.
   b. Map all imports. For each import:
      - Resolve aliases to real paths using the alias map from Step 3.
      - IF resolves to a path inside the project → local dependency (include).
      - IF resolves to `node_modules`, site-packages, or external registry → external (skip).
      - IF ambiguous: check if the path exists on disk. If yes → local. If no → external.
   c. Recursively resolve dependencies of dependencies until reaching leaves (components with no local dependencies).
   d. Build the full dependency graph: `{component: [direct_dependencies]}`.

   NOTE: You read every source file during this step. That source code is now in your context — do NOT re-read it. Label each component's source by name and file path for the subagent prompt.

8. Topological sort: order the graph leaf → root (deepest dependencies first).
   Example: A depends on B and C, B depends on D → order is D, C, B, A.
   This is the analysis order — the agent will analyze components in this sequence.

9. Size guard: compute total source lines across all components.
   IF total exceeds ~8000 lines (~60K tokens): warn the user with exact counts and component count. Offer options: proceed as-is, or split into subtree analyses.
   IF user wants to split: identify natural subtree boundaries and analyze each as a separate `/analyze --recursive` call, bottom-up.

### Step 5: Spawn Analyzer Agent

10. Read the prompt template: `.claude/skills/analyze/analyzer-prompt.md`.
11. Collect each data item listed in **For Orchestrator — Data to Collect** from its specified source. Use the Single Component table or Dependency Tree table based on whether Step 4 ran.
12. Fill `{placeholders}` in **For Subagent — Prompt to Pass** with collected data. Keep purpose descriptions. Include tree-specific sections only for recursive mode. The output format is already embedded in the template.
13. Spawn an **analyzer subagent** (`.claude/agents/analyzer.md`), passing the filled **For Subagent** section as the prompt.

    Single component (no recursion): agent receives one component's source, writes one `.analysis.md`.
    Dependency tree (recursive): agent receives all source + dependency graph + analysis order. Analyzes bottom-up, writes one `.analysis.md` per component sequentially.

### Step 6: Verify Output

14. Parse analyzer text output per `analyzer-prompt.md` § **For Orchestrator — Expected Output**:
    - Read `## Status` → check `**Result**` enum.
      IF not `SUCCESS`: read `## Warnings` for issues. Report to user.
    - Read `## Files Written` table — extract Output Path and Source Hash for each component.

15. Verify every `.analysis.md` that should have been produced:
    For each component (root only in single mode, all components in recursive mode):
    a. Confirm `{component}.analysis.md` exists at the correct path.
    b. Read the frontmatter and verify: `source_hash` is populated, `entry_files` lists all source files, `name`/`type`/`summary` are populated.
    c. IF recursive mode: verify `dependency_tree` is populated with entries for all transitive dependencies.
    d. IF any check fails: report which component's analysis is incomplete and what is missing.

### Step 7: Report to User

16. IF invoked directly by user: show component name, type, one-line summary, key findings (from `## Warnings` if any), and output path.
    IF invoked by another skill (`/execute`, `/plan`): return silently — the calling skill parses the structured output.

---

## Output Format

The analysis document format is defined in the analyzer prompt template (`.claude/skills/analyze/analyzer-prompt.md`). The template contains:
- YAML frontmatter schema (name, type, summary, source_hash, last_analyzed, entry_files, dependency_tree)
- CONTENT section (Purpose & Use Cases, Dependencies, Public API, Integration Patterns, Architecture Diagram, Data Flow, Entrypoints, Patterns Used, Hidden Details)
- EXTRA section (Tests, Performance Notes)

See `.claude/rules/analysis-docs.md` for naming conventions and progressive loading levels.

The analyzer agent's text response follows the output envelope format:
```
## Status
**Result:** SUCCESS | PARTIAL | FAILURE
**Components Analyzed:** {N}
**Files Written:** {N}

## Files Written
| Component | Output Path | Mode | Source Hash |
|-----------|-------------|------|------------|

## Warnings
| Component | Warning | Severity |

## Escalations
| Component | Issue | Severity |
```

---

## Examples

### BAD: Skipping Staleness Check

```
User: /analyze src/services/authService.ts
Orchestrator: [reads source, immediately spawns analyzer, writes new analysis doc]
```

Problems: Did not check if `authService.analysis.md` already exists. If it does and is fresh, this wastes time and tokens regenerating identical content. Always check staleness first.

### BAD: Alias Misclassification in Recursive Mode

```
User: /analyze src/components/Dashboard --recursive
Orchestrator: [maps imports, sees `@/services/dataService`, classifies as external, skips it]
Result: Dashboard.analysis.md missing dataService as a dependency
```

Problems: `@/services/dataService` is a local alias for `src/services/dataService`. By classifying it as external, the orchestrator missed a critical dependency. The analysis doc has an incomplete dependency tree, and cross-component interaction effects are lost.

### GOOD: Full Recursive Analysis Flow

```
User: /analyze src/components/ReportView --recursive

Orchestrator:
1. Resolves path → directory, multi-file module
2. Checks staleness → authService.analysis.md is stale (source changed),
   dataService.analysis.md is fresh
3. Resolves aliases → @/ maps to src/
4. Builds dependency tree:
   ReportView → [DataService, ChartRenderer]
   ChartRenderer → [DataTransformer]
   DataService → [] (leaf)
   DataTransformer → [] (leaf)
5. Topological sort: DataService, DataTransformer, ChartRenderer, ReportView
6. Size check: 4 components, ~1200 lines total → well under 8K limit
7. Spawns analyzer with all source, graph, and order
8. Verifies: 4 .analysis.md files written, all frontmatter populated,
   dependency_tree entries complete
9. Reports: "Analyzed 4 components (ReportView + 3 dependencies).
   Output: src/components/ReportView/ReportView.analysis.md"
```

Why it works: staleness checked first, aliases resolved before classifying, leaf-to-root order enforced, size guard applied, output verified.

---

## Questions This Skill Answers

- "Analyze this component"
- "What does this module do?"
- "Document this service"
- "Build analysis for src/services/auth"
- "Deep dive into this file"
- "Analyze with all dependencies"
- "Is the analysis up to date?"
- "Refresh the analysis doc"
- "What are the hidden behaviors in this component?"
- "Analyze the full dependency tree"
- "I need component intelligence for planning"
- "Create an analysis doc for this"
