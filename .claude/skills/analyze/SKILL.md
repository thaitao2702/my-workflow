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

Check if `{component}.analysis.md` already exists alongside the source:

1. **Does NOT exist** → proceed with **full mode** (Step 3)
2. **Exists** → read the frontmatter, extract `last_commit` and `entry_files`
   - Run: `git log -1 --format=%H -- {entry_files}`
   - Compare the latest commit hash against `last_commit` in frontmatter
   - **MATCH** (doc is current) → report "Analysis is up to date" and STOP
   - **MISMATCH** (code changed) → proceed with **update mode** (Step 3)

## Step 1.5: Resolve Import Aliases

Before mapping dependencies, resolve any path aliases used in the project. Common alias patterns:

1. Check for alias definitions in: `tsconfig.json` (`paths`), `vite.config.*` (`resolve.alias`), `webpack.config.*` (`resolve.alias`), `package.json` (`imports`), `pyproject.toml` (tool-specific), `.eslintrc` (`import/resolver`)
2. Build an alias map, e.g.: `@/ → src/`, `~/ → src/`, `#/ → lib/`
3. When mapping imports in Step 2, resolve aliases to real paths BEFORE classifying as local vs external

**Why:** Aliased imports like `import { auth } from '@/services/authService'` look like external packages but are local code. Treating them as external means skipping their analysis — the component doc will have missing dependency information. Every aliased import that resolves to a path inside the project is a local dependency.

## Step 2: Dependency Resolution (recursive mode only)

Only runs when `--recursive` flag is present.

1. Read the component's source files
2. Map all imports. For each import:
   - Resolve aliases to real paths (using alias map from Step 1.5)
   - If resolves to a path inside the project → **local dependency** (include)
   - If resolves to `node_modules`, site-packages, or external registry → **external** (skip)
   - If ambiguous: check if the path exists on disk. If yes → local. If no → external.
3. Build a dependency tree from all local dependencies
4. Order: **leaf → top** (deepest dependencies first)
   - Example: A depends on B, B depends on C → analyze C first, then B, then A
5. For each dependency (bottom-up):
   - Run the staleness check (Step 1) on the dependency
   - If stale or missing: use the Skill tool to invoke `/analyze` on the dependency path
   - If current: skip (its `.analysis.md` already exists and is up to date)
6. **Critical:** After each dependency is analyzed, its `.analysis.md` now exists on disk. The next dependency in the chain can read it. This guarantees:
   - C is analyzed first → `C.analysis.md` is written
   - B is analyzed next → B's agent receives `C.analysis.md` as dependency context
   - A is analyzed last → A's agent receives both `B.analysis.md` and `C.analysis.md`
7. After ALL dependencies are analyzed, proceed to Step 3 for the original component

## Step 3: Spawn Analyzer Agent

Read the prompt template: `.claude/skills/analyze/analyzer-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source (use the Full Mode or Update Mode table based on Step 1 result)
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions. Omit sections marked *(update mode only)* when in full mode. The output format is already embedded in the template — no need to gather it separately.
3. Spawn an **analyzer subagent** (`.claude/agents/analyzer.md`), passing the filled **For Subagent** section as the prompt

## Step 4: Verify Output

After the agent completes:
1. Confirm `{component}.analysis.md` exists at the correct path
2. Read the frontmatter and verify:
   - `last_commit` matches current `git log -1 --format=%H -- {entry_files}`
   - `entry_files` lists all source files
   - `name`, `type`, `summary` are populated
3. If this is a new major module not in `.workflow/project-overview.md`, suggest adding it

## Step 5: Report to User

If invoked directly by user: show component name, type, key findings, output path.
If invoked by another skill (`/plan`, `/execute`): return silently.

---

## Output Format

The full format spec is embedded in the analyzer prompt template (`.claude/skills/analyze/analyzer-prompt.md`). Below is reference info for consumers of analysis docs.

### Progressive Loading

| Level | What to Read | Tokens | When to Use |
|-------|-------------|--------|-------------|
| **0** | Frontmatter only (first ~10 lines) | ~50 | Scanning dependencies, building project map |
| **1** | Frontmatter + CONTENT section | ~300-500 | Implementing code that interacts with this component |
| **2** | Full document | ~500-800 | Modifying this component's internal code |

### Naming Rules

- Single-file: `{FileName}.analysis.md` next to `{FileName}.{ext}`
- Multi-file module: `{module-name}.analysis.md` at module root
- `entry_files` in frontmatter lists which source files belong to the component
