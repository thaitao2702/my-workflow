# Doc-Updater Prompt Template

## For Orchestrator — Data to Collect

### Shared Data (sent once)

| Data | Source |
|------|--------|
| Project overview | `.workflow/project-overview.md` |
| Plan context | Plan summary + what was being built and why. Omit if manual invocation. |

### Per-Component Data (for each component in assessment list)

| Data | Source |
|------|--------|
| Git diff | `git diff` scoped to this component's changed files |
| Existing analysis | Full content of the existing `.analysis.md` file |
| Entry files | The component's `entry_files` from the existing analysis frontmatter (needed for hash computation) |
| Output path | Path to the `.analysis.md` file (for MINOR patches) |
| Discoveries | From manifest row, or "—" if none. Omit if manual invocation. |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions. Repeat the per-component block for each component. Pass everything below this line as the subagent prompt.

**Project Overview:**
{project_overview}
Codebase architecture and conventions. Use to judge whether changes affect project-level concerns.

**Plan Context:** *(omit section if not available)*
{plan_context}
What was being built and why. Sharpens your significance judgment — "3 new fields" could be MINOR (additive feature) or MAJOR (data flow change). The plan intent disambiguates.

**Components to assess:**

### {component_path_1}

**Git Diff:**
{git_diff_1}
The code changes for this component. Base your classification on this — every claim must trace back to something in the diff.

**Existing Analysis:**
{existing_analysis_1}
The current `.analysis.md` content. For MINOR updates, patch this document surgically — add rows, update fields, don't rewrite sections that are still accurate.

**Entry Files:** `{entry_files_1}`
The component's source files. For MINOR updates, recompute `source_hash` by running: `python .claude/scripts/workflow_cli.py hash {entry_files}`

**Output Path:** `{output_path_1}`
If you classify as MINOR_UPDATE, write the patched analysis to this path.

**Discoveries:** *(omit if none)*
{discoveries_1}
Findings the executor reported about THIS component — hidden behaviors, wrong assumptions, edge cases. Incorporate into the Hidden Details table during MINOR patches, or flag for `/analyze` if MAJOR.

### {component_path_2}
{... same per-component structure ...}

**Your Task:**

For EACH component listed above:
1. **Classify** as NO_UPDATE, MINOR_UPDATE, or MAJOR_UPDATE (see your agent instructions for criteria)
2. **Act** based on classification:
   - NO_UPDATE with no discoveries → no file changes
   - NO_UPDATE with discoveries → treat as MINOR_UPDATE (experiential knowledge must be recorded)
   - MINOR_UPDATE → patch the existing analysis at the output path (add table rows, update frontmatter `source_hash` and `last_analyzed`, update `summary` only if component purpose expanded). Also add any executor discoveries to the Hidden Details table.
   - MAJOR_UPDATE → do NOT attempt a full rewrite
3. **Respond** using the output format below

Process components in the order listed. Do NOT skip any component.

## Output Format

Follow this format exactly:

```
## Status
**Result:** SUCCESS | PARTIAL | FAILURE
**Components Assessed:** {N}
**Breakdown:** NO_UPDATE: {N}, MINOR_UPDATE: {N}, MAJOR_UPDATE: {N}

## Components
### {component_path}
**Classification:** NO_UPDATE | MINOR_UPDATE | MAJOR_UPDATE
**Reasoning:**
- {bullet — must trace to diff}
**Actions Taken:**
| Action | Target Section | Detail |
|--------|---------------|--------|
| added_row ∣ updated_field ∣ updated_hash ∣ added_discovery | {section name} | {what changed} |
**Escalation:** NONE | ANALYZE_REQUIRED
**Discoveries to Pass:** [{findings for analyzer}]

## Escalations
| Component | Reason | Discoveries |
|-----------|--------|-------------|
| {path} | {why MAJOR} | [{findings to pass to /analyze}] |
```

- **Status.Result:** `SUCCESS` = all components assessed. `PARTIAL` = some components assessed, others failed. `FAILURE` = assessment couldn't complete.
- **Actions Taken:** One row per action performed. Write "None" (no table) for NO_UPDATE with no discoveries.
- **Discoveries to Pass:** Only include if Escalation is ANALYZE_REQUIRED. Lists findings the analyzer needs.
- **Escalations:** Summary of all components requiring `/analyze`. Write "None" if no MAJOR_UPDATE components.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: SUCCESS ∣ PARTIAL ∣ FAILURE | Verify assessment completed |
| | `**Breakdown**`: count per classification | Quick summary — how many need action |
| `## Components` | Per component: `**Classification**`, `**Escalation**` | Route: NO_UPDATE → skip, MINOR_UPDATE → verify, MAJOR_UPDATE → invoke `/analyze` |
| | `**Actions Taken**` table | Verify patches were applied correctly |
| | `**Discoveries to Pass**` | Feed to `/analyze` if ANALYZE_REQUIRED |
| `## Escalations` | Table: Component, Reason, Discoveries | List of components needing `/analyze` invocation |
