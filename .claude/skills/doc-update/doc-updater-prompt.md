# Doc-Updater Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect all before constructing the prompt.

| Data | Source |
|------|--------|
| Git diff | `git diff` for the component's files (scoped to this component, not the full repo diff) |
| Existing analysis | Full content of the existing `.analysis.md` file |
| Project overview | `.workflow/project-overview.md` |
| Plan context | Plan summary + what was being built and why (from calling skill's context). Omit if manual invocation. |
| Output path | Path to the `.analysis.md` file (for MINOR patches) |

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

**Output Path:** `{output_path}`
If you classify as MINOR UPDATE, write the patched analysis to this path.

**Your Task:**

1. **Classify** the changes as NO UPDATE, MINOR UPDATE, or MAJOR UPDATE (see your agent instructions for criteria)
2. **Act** based on classification:
   - NO UPDATE → report classification only, no file changes
   - MINOR UPDATE → patch the existing analysis at the output path (add table rows, update frontmatter `last_commit` and `last_analyzed`, update `summary` only if component purpose expanded)
   - MAJOR UPDATE → report classification and recommend `/analyze` trigger (do NOT attempt a full rewrite)
3. **Report** your classification, reasoning, and any actions taken
