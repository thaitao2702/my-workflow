# Dependency Resolver Prompt Template

## For Orchestrator — Data to Collect

| Data | Source |
|------|--------|
| Entry component path | User input or plan task — path to the component file |
| Project root | Working directory — base for config resolution and project boundary |
| Language | *(optional)* Override auto-detection. Valid: `javascript`, `python`, `go`, `rust`, `java`, `kotlin`, `cpp`, `ruby`, `php` |
| Alias map | *(optional)* Pre-resolved config from a previous run. Skip config discovery. |
| Max depth | *(optional)* Integer recursion limit. Default: unlimited (100-node safety cap). |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Pass everything below this line as the subagent prompt.

**Entry Component:** `{entry_component_path}`
The starting file. Build the full transitive dependency tree from this file's imports, recursively.

**Project Root:** `{project_root}`
Base directory for config files and project boundary. A file is "local" if it lives under this root.

**Language:** *(omit if not provided)*
{language}
Override auto-detection. Apply this language's resolution strategy for the entire traversal.

**Alias Map:** *(omit if not provided)*
{alias_map}
Pre-resolved path/module config. Format: `{prefix: resolved_base_path}`. Skip config discovery.

**Max Depth:** *(omit if not provided)*
{max_depth}
Maximum recursion depth. Default: full tree (100-node safety cap).

## Instructions

Build a dependency tree from the entry component. Detect the language, discover config, walk imports recursively, report the graph.

1. **Verify** entry file exists. If not → FAILURE.
2. **Detect language** from file extension (or use override). Unknown extension → FAILURE.
3. **Discover config** — scan language-appropriate config files (tsconfig, go.mod, Cargo.toml, pyproject.toml, build.gradle/pom.xml, CMakeLists.txt, composer.json, Gemfile). Extract aliases, module paths, or source roots.
4. **Walk imports** — for each file: extract imports, classify local vs. external, resolve local to file paths, add to graph. Track visited files. Stop at 100 nodes or max depth.
5. **Detect cycles** — DFS with recursion stack after traversal.
6. **Report** — assemble output.

**Rules:**
- Only LOCAL project source files. Never follow into `node_modules`, `site-packages`, system includes, etc.
- One language strategy for the entire traversal — do not mix.
- Re-exports are dependency edges (JS `export from`, Python `__init__.py`, Rust `pub use`).
- For non-relative imports, resolve via source roots / module config before classifying as external.
- Stop at 100 nodes or `max_depth` and report partial results.

## Output Format

**CRITICAL:** The orchestrator only receives your final text. Follow this format exactly.

```
## Status
**Result:** SUCCESS | PARTIAL | FAILURE
**Nodes Discovered:** {N}
**Cycles Detected:** {N}
**Entry Component:** {path}
**Detected Language:** {language}

## Dependency Graph
| Component | Direct Dependencies |
|-----------|-------------------|
| {file_path} | [{dependency_paths}] |

**Cycles:** *(omit if none)*
| Cycle | Members |
|-------|---------|
| {N} | [{paths}] |

## Alias Map
| Prefix | Resolved Base Path | Source |
|--------|--------------------|--------|
| {alias} | {path} | {config file name ∣ provided} |

## Unresolved Imports
| Import Specifier | Importing File | Probes Attempted |
|-----------------|----------------|-----------------|
| {specifier} | {file} | [{tried}] |

## Escalations
| Type | Description | Severity |
|------|-------------|----------|
| circular_dependency ∣ alias_config_missing ∣ unresolved_import ∣ tree_too_large ∣ unsupported_language | {details} | info ∣ warning |
```

- **Result:** `SUCCESS` = full tree, no issues. `PARTIAL` = tree built with unresolved imports, cycles, or truncated. `FAILURE` = entry not found or unsupported language.
- **Dependency Graph:** One row per file. Direct dependencies only (not transitive). Project-relative paths.
- **Alias Map:** Config used. "None" if no config.
- **Unresolved Imports:** Local-looking imports that resolved to no file. "None" if all resolved.
- **Escalations:** "None" if no issues.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: SUCCESS ∣ PARTIAL ∣ FAILURE | Fast triage |
| | `**Nodes Discovered**`: integer | Tree size sanity check |
| | `**Cycles Detected**`: integer | If >0, review cycles before passing to analyzer |
| | `**Detected Language**`: string | Pass to downstream agents |
| `## Dependency Graph` | Table: Component, Direct Dependencies | Pass to analyzer as `{dependency_graph}` |
| | Cycles table *(if present)* | Warn user about circular dependencies |
| `## Alias Map` | Table: Prefix, Resolved Base Path, Source | Cache for subsequent invocations |
| `## Unresolved Imports` | Table: Import Specifier, Importing File, Probes | Surface to user — may indicate missing files or config issues |
| `## Escalations` | Table: Type, Description, Severity | Handle `warning` before proceeding |
