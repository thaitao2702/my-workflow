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
**Dependency Resolution:** dependency graph (adjacency list), dependency-resolver agent, cycle detection, local-external boundary, alias map caching, multi-language import resolution, parallel agent spawning
**Analysis Artifacts:** `.analysis.md` schema, YAML frontmatter (source_hash, entry_files, last_analyzed, dependency_tree, analysis_version), Hidden Details table, Integration Patterns section, Architecture/Data Flow diagrams (Mermaid)
**Orchestration:** prompt template filling (agent I/O contract), output envelope parsing, topological sort (leaf-to-root), size guard (context window management), bottom-up analysis order, verification checklist

---

## Anti-Pattern Watchlist

### 1. Stale Analysis Accepted
**Detection:** Proceeding with an existing analysis doc without running `analysis check`. Orchestrator skips staleness check "because the file exists."
**Resolution:** Always run the CLI `analysis check` command before deciding mode. Fresh → stop. Stale → re-analyze. Hash check is the single source of truth for freshness.

### 2. Resolver Escalation Ignored
**Detection:** Dependency-resolver reports cycles, unresolved imports, or `alias_config_missing` — orchestrator proceeds without surfacing to user or adjusting the analysis plan.
**Resolution:** Always parse `## Escalations` from the resolver output. Cycles → warn user, ask whether to proceed (cycles may cause incomplete cross-component analysis). Unresolved imports → warn user (missing deps mean incomplete tree). `alias_config_missing` → warn that non-relative imports may be misclassified.

### 3. Out-of-Order Analysis
**Detection:** Components passed to the analyzer in wrong order — a dependent analyzed before its dependencies. The topological sort was skipped or computed incorrectly from the dependency graph.
**Resolution:** Compute topological sort from the dependency-resolver's adjacency list. Verify: every component appears AFTER all its direct dependencies in the order. Pass this order to the analyzer's `{analysis_order}` placeholder.

### 4. Context Overflow Without Guard
**Detection:** Large dependency trees (>8000 lines, ~60K tokens) passed to the analyzer without warning. Analyzer output quality degrades silently due to context saturation.
**Resolution:** Compute total source lines before spawning the analyzer. IF exceeds ~8000 lines: warn user with exact counts and offer to split into subtree analyses.

### 5. Unverified Output
**Detection:** Analyzer results accepted without checking that `.analysis.md` files were actually written, or that frontmatter fields are populated. Missing files or empty fields go unnoticed.
**Resolution:** After the analyzer completes, verify every expected `.analysis.md` exists. Read frontmatter, confirm all required fields. Report any failures.

### 6. Serial Resolution for Parallel Entries
**Detection:** Multiple entry components resolved one-by-one. The second dependency-resolver waits for the first to finish when they have no dependency on each other.
**Resolution:** Spawn one dependency-resolver agent per entry component. If multiple entries, spawn all in parallel. Cache the alias map from the first to complete and pass to subsequent analyzer invocations.

### 7. Single-File Recursive Overhead
**Detection:** Full dependency resolution machinery runs for a leaf component that has zero local dependencies. Dependency-resolver returns a single node.
**Resolution:** After receiving the dependency graph, IF graph contains only the root with no dependencies: fall back to single-component mode. Inform user: "No local dependencies found — analyzing as single component."

---

## Behavioral Instructions

### Step 1: Parse Input

1. Extract component path(s) from the user's input. One or multiple paths supported.
2. Check for `--recursive` flag.
3. Resolve each path:
   IF path points to a file → single-file component. Output path: `{FileName}.analysis.md` next to the file.
   IF path points to a directory → multi-file module. Output path: `{module-name}.analysis.md` at the module root.

---CHECKPOINT---
Done: Parsed input — {N} component(s), recursive={yes/no}
Next: Step 2 — check staleness for each component. Run CLI `analysis check` to determine if analysis docs are fresh, stale, or missing. Fresh entries are skipped entirely.
User directives: {any corrections from user, or "None"}
---END CHECKPOINT---

### Step 2: Staleness Check

4. For each entry component, check if `{component}.analysis.md` already exists at the resolved output path.

   IF no analysis doc exists → proceed (needs full analysis).

   IF analysis doc exists → run CLI `analysis check` command (add `--recursive` if recursive mode):
   - `fresh` → report "Analysis is up to date for {component}" and SKIP this entry.
   - `stale` → note reason and which files/deps changed. Proceed.
   - `missing` → treat as full mode. Proceed.

   IF all entries are fresh → STOP. Nothing to do.

---CHECKPOINT---
Done: Staleness check complete — {N} entries need analysis, {M} skipped (fresh)
Next: Step 3 — resolve dependencies. For each entry needing analysis, spawn a dependency-resolver agent (Haiku) to build the dependency tree. If not recursive mode, skip to Step 4 (single-mode preparation).
User directives: {any corrections from user, or "None"}
---END CHECKPOINT---

### Step 3: Resolve Dependencies

5. IF `--recursive` flag is NOT present: skip to Step 4.

6. For each entry component that needs analysis:
   a. Read `dependency-resolver-prompt.md` → collect data per **For Orchestrator — Data to Collect**: entry component path, project root. Optionally pass alias map if cached from a previous resolver run.
   b. Fill `{placeholders}` in **For Subagent — Prompt to Pass**.
   c. Spawn a **dependency-resolver** agent (`.claude/agents/dependency-resolver.md`, model: Haiku).
   IF multiple entries → spawn all dependency-resolver agents **in parallel**.

7. Parse each resolver's output per `dependency-resolver-prompt.md` § **For Orchestrator — Expected Output**:
   a. Read `## Status` → check `**Result**`.
      IF `FAILURE` → report error to user. Remove this entry from analysis queue.
      IF `PARTIAL` → proceed with partial tree, warn user.
   b. Extract `## Dependency Graph` table → the adjacency list for this entry's tree.
   c. Extract `## Alias Map` → cache it. Pass to subsequent resolver/analyzer invocations.
   d. Read `## Escalations`:
      - `circular_dependency` → warn user with cycle members. Ask: proceed with cycle members analyzed in listed order, or skip cycle members?
      - `unresolved_import` → warn user. These dependencies will be missing from analysis.
      - `alias_config_missing` → warn user that non-relative imports may be misclassified.
      - `tree_too_large` → warn user with node count. Offer to analyze subtrees separately.
   e. IF dependency graph contains only the root with zero dependencies → fall back to single-component mode for this entry. Inform user.

8. For each dependency graph, compute topological sort (leaf → root):
   - Build in-degree map from adjacency list.
   - Repeatedly select nodes with in-degree 0, append to order, decrement dependents' in-degrees.
   - Result: analysis order where every component appears after all its dependencies.
   WHY: the dependency-resolver only produces the graph. Ordering is the orchestrator's job — the analyzer needs a flat list to follow sequentially.

---CHECKPOINT---
Done: Dependencies resolved — {N} trees built, {M} total components across all trees
Next: Step 4 — prepare analysis context. For each tree: collect source code for all components, find test files, compute total line count for size guard, determine output paths.
User directives: {any corrections from user, or "None"}
---END CHECKPOINT---

### Step 4: Prepare Analysis Context

9. For each entry's dependency tree (or single component):
   a. Read source files for every component in the tree. Label each by component name and file path for the analyzer prompt.
   b. Find test files for each component (co-located tests, `__tests__/` dirs, `*_test.*`, `*.spec.*`). Include if they exist.
   c. Determine output path for each component's `.analysis.md` (co-located per naming convention in `.claude/rules/analysis-docs.md`).
   d. Read `.workflow/project-overview.md` (shared across all entries).
   e. IF single-mode entry with an existing stale analysis doc → read it for the analyzer's `{existing_analysis}` placeholder.

10. Size guard: compute total source lines across all components in each tree.
    IF total exceeds ~8000 lines (~60K tokens): warn user with exact counts and component count. Offer options: proceed as-is, or split into subtree analyses.

---CHECKPOINT---
Done: Analysis context prepared — source collected, size guard passed
Next: Step 5 — spawn analyzer agents. For each entry, fill the analyzer prompt template with collected data (mode, graph, order, source, test files, output paths) and spawn an analyzer subagent (Opus).
User directives: {any corrections from user, or "None"}
---END CHECKPOINT---

### Step 5: Spawn Analyzer

11. Read `analyzer-prompt.md`.
12. For each entry component, collect data per **For Orchestrator — Data to Collect** (use Single Component or Dependency Tree table based on mode):

    **Single mode:** mode=`single`, component source, test files, existing analysis (if stale update), project overview, output path.

    **Tree mode:** mode=`tree`, dependency graph (from Step 3), analysis order (from Step 3 topological sort), all source code (labeled, from Step 4), test files, project overview, output paths for each component.

13. Fill `{placeholders}` in **For Subagent — Prompt to Pass**. Include tree-specific sections only for tree mode.
14. Spawn an **analyzer** agent (`.claude/agents/analyzer.md`, model: Opus), passing the filled prompt.
    One analyzer per entry component's tree. The analyzer handles bottom-up execution internally:
    - Reads dependency graph and analysis order
    - Analyzes leaf components first, writes their `.analysis.md`
    - Moves to components that depend on analyzed leaves
    - Continues up the tree until the root is analyzed
    - Cross-component insights accumulate — by the time it reaches the root, it understands the full stack

### Step 6: Verify Output

15. Parse analyzer text output per `analyzer-prompt.md` § **For Orchestrator — Expected Output**:
    - Read `## Status` → check `**Result**`.
      IF not `SUCCESS`: read `## Warnings` for issues. Report to user.
    - Read `## Files Written` table → extract Output Path and Source Hash for each component.

16. Verify every `.analysis.md` that should have been produced:
    For each component (root only in single mode, all components in tree mode):
    a. Confirm `{component}.analysis.md` exists at the correct path.
    b. Read frontmatter — verify: `source_hash` is populated, `entry_files` lists all source files, `name`/`type`/`summary` are populated.
    c. IF tree mode: verify `dependency_tree` is populated with entries for all transitive dependencies.
    d. IF any check fails: report which component's analysis is incomplete and what is missing.

---CHECKPOINT---
Done: Output verified — {N} analysis docs confirmed
Next: Step 7 — report results to user.
User directives: {any corrections from user, or "None"}
---END CHECKPOINT---

### Step 7: Report to User

17. IF invoked directly by user: show component name, type, one-line summary, key findings (from `## Warnings` if any), and output path.
    IF invoked by another skill (`/execute`, `/plan`): return silently — the calling skill parses the structured output.

---

## Output Format

The analysis document format is defined in the analyzer prompt template (`analyzer-prompt.md`). See `.claude/rules/analysis-docs.md` for naming conventions and progressive loading levels.

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

### BAD: Ignoring Resolver Escalation

```
User: /analyze src/components/Dashboard --recursive

Orchestrator:
1. Spawns dependency-resolver
2. Resolver returns: Result=PARTIAL, Cycles Detected=1,
   Escalation: circular_dependency between Dashboard↔Widget
3. Orchestrator ignores escalation, passes graph to analyzer as-is
4. Analyzer produces incomplete cross-component analysis for the cycle
```

Problem: The circular dependency escalation was not surfaced. User never learned about the cycle. Analyzer couldn't properly build bottom-up understanding through the cycle.

### BAD: Serial Dependency Resolution

```
User: /analyze src/services/auth.ts src/services/payment.ts --recursive

Orchestrator:
1. Spawns dependency-resolver for auth.ts, waits for result
2. Spawns dependency-resolver for payment.ts, waits for result
3. Total time: resolver_1 + resolver_2
```

Problem: The two entries are independent. Both resolvers should spawn in parallel, cutting wall time in half.

### GOOD: Full Recursive Analysis Flow

```
User: /analyze src/components/ReportView --recursive

Orchestrator:
1. Resolves path → directory, multi-file module
2. Staleness check → stale (source changed)
3. Spawns dependency-resolver agent (Haiku):
   - Returns graph: ReportView → [ChartRenderer, DataService]
                    ChartRenderer → [DataTransformer]
                    DataService → []
                    DataTransformer → []
   - Returns alias map: @/ → src/
   - No escalations
4. Computes topological sort: DataService, DataTransformer, ChartRenderer, ReportView
5. Collects source for all 4 components (~1200 lines, under 8K limit)
6. Spawns analyzer agent (Opus) in tree mode:
   - Analyzer processes leaf → root: DataService first, then DataTransformer,
     then ChartRenderer (can reference DataTransformer analysis),
     then ReportView (understands full stack)
   - Writes 4 .analysis.md files
7. Verifies: 4 files written, all frontmatter populated, dependency_tree entries complete
8. Reports: "Analyzed 4 components (ReportView + 3 dependencies)"
```

### GOOD: Multi-Entry Parallel Resolution

```
User: /analyze src/services/auth.ts src/services/payment.ts --recursive

Orchestrator:
1. Staleness check → both stale
2. Spawns 2 dependency-resolver agents IN PARALLEL:
   - auth.ts resolver → graph with 3 nodes, alias map cached
   - payment.ts resolver → graph with 5 nodes (reuses alias map)
3. Computes topological sort for each tree
4. Spawns 2 analyzer agents (sequential — may share components):
   - auth tree: 3 components bottom-up
   - payment tree: 5 components bottom-up (skips already-analyzed shared deps)
5. Verifies all analysis docs
```

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
