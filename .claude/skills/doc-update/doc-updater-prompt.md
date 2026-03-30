# Doc-Updater Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect all before constructing the prompt.

| Data | Source |
|------|--------|
| Git diff | `git diff` for the component's files (scoped to this component, not the full repo diff) |
| Existing analysis | Full content of the existing `.analysis.md` file |
| Project overview | `.workflow/project-overview.md` |
| Plan context | Plan summary + what was being built and why (from calling skill's context). Omit if manual invocation. |
| Entry files | The component's `entry_files` from the existing analysis frontmatter (needed for hash computation) |
| Output path | Path to the `.analysis.md` file (for MINOR patches) |
| Executor discoveries | Findings from executor `## Discoveries` sections that are relevant to THIS component. Omit if none or if manual invocation. |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions. Pass everything below this line as the subagent prompt.

**Git Diff:**
{git_diff}
The code changes to assess. Base your classification on this — every claim must trace back to something in the diff.

**Existing Analysis:**
{existing_analysis}
The current `.analysis.md` content. For MINOR updates, patch this document surgically — add rows, update fields, don't rewrite sections that are still accurate.

**Project Overview:**
{project_overview}
Codebase architecture and conventions. Use to judge whether changes affect project-level concerns.

**Plan Context:** *(omit section if not available)*
{plan_context}
What was being built and why. Sharpens your significance judgment — "3 new fields" could be MINOR (additive feature) or MAJOR (data flow change). The plan intent disambiguates.

**Entry Files:** `{entry_files}`
The component's source files. For MINOR updates, recompute `source_hash` by running: `python .claude/scripts/workflow_cli.py hash {entry_files}`

**Output Path:** `{output_path}`
If you classify as MINOR UPDATE, write the patched analysis to this path.

**Executor Discoveries:** *(omit section if not available)*
{discoveries}
Findings the executor reported about THIS component during implementation — hidden behaviors, wrong assumptions, edge cases, integration gotchas. These are experiential knowledge not visible in the diff alone. Incorporate them into the analysis doc (Hidden Details table) during MINOR patches, or flag them for the full `/analyze` if MAJOR.

**Your Task:**

1. **Classify** the changes as NO UPDATE, MINOR UPDATE, or MAJOR UPDATE (see your agent instructions for criteria)
2. **Act** based on classification:
   - NO UPDATE with no discoveries → report classification only, no file changes
   - NO UPDATE with discoveries → treat as MINOR UPDATE (the code didn't change enough to affect docs, but we learned something new that must be recorded)
   - MINOR UPDATE → patch the existing analysis at the output path (add table rows, update frontmatter `source_hash` and `last_analyzed`, update `summary` only if component purpose expanded). Also add any executor discoveries to the Hidden Details table.
   - MAJOR UPDATE → report classification and recommend `/analyze` trigger (do NOT attempt a full rewrite). List discoveries so the analyzer can incorporate them.
3. **Report** your classification, reasoning, and any actions taken
