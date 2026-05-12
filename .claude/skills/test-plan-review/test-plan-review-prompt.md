# Test Plan Review Echo Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Mirrors the plan-reviewer-prompt.md placeholders exactly.

| Placeholder | Source | Format Convention (agent-contracts.md) |
|-------------|--------|---------------------------------------|
| `{$PLAN_DIR}` | Any existing plan directory path | Single path |
| `{planning_rules_dir}` | `.workflow/rules/planning/` — pass directory path, or `None` if it doesn't exist | Single path or None |
| `{component_doc_paths}` | Any `.analysis.md` file paths, or `None` if none exist | Path list or None |
| `{source_file_paths}` | 2-3 real source file paths from the project | Path list |
| `{project_overview_path}` | `.workflow/project-overview.md` or substitute if missing | Single path |
| `{output_path}` | `.workflow/test-plan-review-output/prompt-received.md` | Single path |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep all structure and instructions. Pass everything below the `---` line as the subagent prompt.

---

**Output Path:** {output_path}
Write the full prompt you receive to this file. Create parent directories if needed.

**Plan Directory:** {$PLAN_DIR}

**Step 1: Note the CLI command (DO NOT execute it).**

This command contains the plan directory path in a different context than the header above:
```
python .claude/scripts/workflow_cli.py plan review-dump --plan-dir {$PLAN_DIR}
```
Note whether the plan-dir value here matches the "Plan Directory" value above — they should be identical strings.

**Step 2: Note context file paths.**

| Category | Paths | Purpose |
|----------|-------|---------|
| Component docs | {component_doc_paths} | Test: path list placeholder (bare in template) |
| Source files | {source_file_paths} | Test: path list placeholder (bare in template) |
| Project overview | {project_overview_path} | Test: single path placeholder (bare in template) |
| Planning rules | {planning_rules_dir} | Test: single path or None (bare in template) |

**Step 3: Echo all values.**

Parse each placeholder from the sections above and report them in the output format below. Do NOT execute any commands or load any files. Report EXACT strings as received.

## Output Format

Follow this format exactly:

```
## Status
**Result:** ECHO_COMPLETE
**Placeholder Count:** 6

## Placeholder Values
| # | Placeholder | Context | Received Value | Has Backticks | Double Wrapped |
|---|-------------|---------|---------------|---------------|----------------|
| 1 | $PLAN_DIR | Header ("Plan Directory:" line) | {exact value} | YES/NO | YES/NO |
| 2 | $PLAN_DIR | CLI command (--plan-dir arg) | {exact value} | YES/NO | YES/NO |
| 3 | component_doc_paths | Table: Component docs row | {exact value} | YES/NO | YES/NO |
| 4 | source_file_paths | Table: Source files row | {exact value} | YES/NO | YES/NO |
| 5 | project_overview_path | Table: Project overview row | {exact value} | YES/NO | YES/NO |
| 6 | planning_rules_dir | Table: Planning rules row | {exact value} | YES/NO | YES/NO |

## Format Analysis
**Header/CLI plan-dir consistency:** MATCH/MISMATCH — {details}
**Path list formatting:** {describe: are paths comma-separated? backtick-wrapped individually?}
**Single path formatting:** {describe: single backtick or double backtick wrapping?}
**Double wrapping detected:** YES/NO — {list which placeholders if YES}

## Escalations
| Type | Placeholder | Description |
|------|-------------|-------------|
| format_issue ∣ consistency_issue ∣ convention_violation | {name} | {details} |
```

- **Status.Result:** Always `ECHO_COMPLETE` — this agent does not fail
- **Placeholder Values:** One row per placeholder occurrence. Report exact received value.
- **Format Analysis:** Synthesize findings across all placeholders
- **Escalations:** Every format issue, mismatch, or convention violation. `None` if all clean.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: ECHO_COMPLETE | Confirm agent completed |
| `## Placeholder Values` | Table with received values per placeholder | Verify each placeholder received correct value |
| `## Format Analysis` | Consistency and formatting checks | Detect double wrapping, mismatches |
| `## Escalations` | Table: Type, Placeholder, Description | All format issues — primary finding output |
