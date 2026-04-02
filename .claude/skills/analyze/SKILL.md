---
description: "Deep-analyze a component — capture hidden knowledge, business logic, integration patterns"
---

# /analyze — Component Analysis

Deep, narrow analysis of a specific component. Produces co-located documentation that any AI agent can consume.

**Input:** `/analyze {component-path}` or `/analyze {component-path} --recursive`
**Output:** `{ComponentName}.analysis.md` co-located alongside the source file(s)

## Step 0: Parse Input

- Extract the component path from the user's input
- Check for `--recursive` flag
- Resolve the path to identify:
  - **Single-file component:** path points to a file → `{FileName}.analysis.md` next to it
  - **Multi-file module:** path points to a directory → `{module-name}.analysis.md` at the module root

## Step 1: Staleness Check

Check if `{component}.analysis.md` already exists alongside the source.

### No analysis doc → Full mode (Step 2 or Step 3)

If `--recursive`: proceed to Step 2 (dependency resolution).
If not recursive: proceed to Step 3 (single-component analysis).

### Analysis doc exists → Hash-based staleness check

Use the CLI `analysis check` command (add `--recursive` if in recursive mode).

- **`fresh`** → analysis is up to date → report "Analysis is up to date" and STOP
- **`stale`** → the response includes the reason and which files/deps changed → proceed to Step 2 (recursive) or Step 3 (single-component)
- **`missing`** → should not happen in this branch (analysis doc exists), but treat as full mode

## Step 1.5: Resolve Import Aliases

Before mapping dependencies, resolve any path aliases used in the project. Common alias patterns:

1. Check for alias definitions in: `tsconfig.json` (`paths`), `vite.config.*` (`resolve.alias`), `webpack.config.*` (`resolve.alias`), `package.json` (`imports`), `pyproject.toml` (tool-specific), `.eslintrc` (`import/resolver`)
2. Build an alias map, e.g.: `@/ → src/`, `~/ → src/`, `#/ → lib/`
3. When mapping imports in Step 2, resolve aliases to real paths BEFORE classifying as local vs external

**Why:** Aliased imports like `import { auth } from '@/services/authService'` look like external packages but are local code. Treating them as external means skipping their analysis — the component doc will have missing dependency information. Every aliased import that resolves to a path inside the project is a local dependency.

## Step 2: Dependency Resolution + Source Collection (recursive mode only)

Only runs when `--recursive` flag is present. This step prepares everything for a single-agent analysis of the entire dependency tree.

### Step 2a: Build Dependency Tree + Collect Source

1. Read the component's source files
2. Map all imports. For each import:
   - Resolve aliases to real paths (using alias map from Step 1.5)
   - If resolves to a path inside the project → **local dependency** (include)
   - If resolves to `node_modules`, site-packages, or external registry → **external** (skip)
   - If ambiguous: check if the path exists on disk. If yes → local. If no → external.
3. Recursively resolve dependencies of dependencies until reaching leaves (components with no local dependencies)
4. Build the full dependency graph: `{component: [direct_dependencies]}`

**Note:** You read every source file during dependency resolution. That source code is now in your context — do NOT re-read it. Label each component's source by name and file path for the subagent prompt.

### Step 2b: Topological Sort

Order the graph **leaf → root** (deepest dependencies first).

Example: A depends on B and C, B depends on D → order is D, C, B, A (C and D are both leaves, either order is fine).

This is the **analysis order** — the agent will analyze components in this sequence.

### Step 2c: Size Guard

If total source code exceeds ~8000 lines (~60K tokens):
- Warn the user: "Dependency tree has {N} components totaling ~{lines} lines. This may strain context. Options: proceed, or I can analyze subtrees separately."
- If user wants to split: identify natural subtree boundaries and analyze each subtree as a separate `/analyze --recursive` call, bottom-up.

### Step 2d: Proceed to Step 3

Pass to Step 3: the dependency graph, analysis order, and all source code (already in context from Step 2a).

## Step 3: Spawn Analyzer Agent

Read the prompt template: `.claude/skills/analyze/analyzer-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source (use the Single Component or Dependency Tree table based on whether Step 2 ran)
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions. Include tree-specific sections only for recursive mode. The output format is already embedded in the template.
3. Spawn an **analyzer subagent** (`.claude/agents/analyzer.md`), passing the filled **For Subagent** section as the prompt

**Single component (no recursion):** Agent receives one component's source, writes one `.analysis.md`.
**Dependency tree (recursive):** Agent receives all source + dependency graph + analysis order. Analyzes bottom-up, writes one `.analysis.md` per component sequentially.

## Step 4: Verify Output

**Parse analyzer text output** per `analyzer-prompt.md` § "For Orchestrator — Expected Output":
- Read `## Status` → `**Result**`: if not `SUCCESS`, check `## Warnings` for issues
- Read `## Files Written` table — use Output Path and Source Hash for verification below

After the agent completes, verify **every** `.analysis.md` that should have been produced:

For each component (just the root in single mode, all components in recursive mode):
1. Confirm `{component}.analysis.md` exists at the correct path
2. Read the frontmatter and verify:
   - `source_hash` is populated
   - `entry_files` lists all source files
   - `name`, `type`, `summary` are populated
3. For recursive mode: verify `dependency_tree` is populated with entries for all transitive dependencies
4. If any check fails: report which component's analysis is incomplete

## Step 5: Report to User

If invoked directly by user: show component name, type, key findings, output path.
If invoked by another skill (`/execute`): return silently.

---

## Output Format

The full format spec is embedded in the analyzer prompt template (`.claude/skills/analyze/analyzer-prompt.md`). Below is reference info for consumers of analysis docs.

See `.claude/rules/analysis-docs.md` for naming conventions and progressive loading levels.
