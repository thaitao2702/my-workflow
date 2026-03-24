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

Use the Agent tool to spawn `.claude/agents/analyzer.md`.

### For Full Mode

Provide in the agent prompt:
- Mode: `full`
- Component source code (all files in the module, or the single entry file)
- Test files for this component (if they exist)
- Dependency `.analysis.md` files (frontmatter + CONTENT section only) — **read these fresh from disk**, they were just written/confirmed current in Step 2
- Project overview: `.workflow/project-overview.md`
- Output path: the co-located `.analysis.md` path determined in Step 0
- The **output format** below

### For Update Mode

Provide in the agent prompt:
- Mode: `update`
- The existing `.analysis.md` file (full content)
- Git diff: `git diff {last_commit}..HEAD -- {entry_files}`
- Current source code (all entry files)
- Dependency `.analysis.md` files (frontmatter + CONTENT section only) — **read fresh from disk**
- Project overview: `.workflow/project-overview.md`
- Output path: same file location (overwrite)
- The **output format** below

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

Pass this format to the analyzer agent. The agent writes the file.

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
