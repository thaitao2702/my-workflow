# Test Echo Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect PATHS only — the subagent reads files itself.

| Data | Source | Pass as |
|------|--------|---------|
| Output path | `.workflow/test-io-output/prompt-received.md` | Path |
| Project overview path | `.workflow/project-overview.md` | Path |
| Analysis doc paths | Any `.analysis.md` files that exist in the project | Paths (list) |
| Source file paths | 2-3 real source files from the project | Paths (list) |
| Rule file paths | `.claude/rules/quality-criteria.md`, `.claude/rules/tdd-policy.md` | Paths (list) |
| Computed value (test) | A short string like "This is a computed value that has no file on disk" | Content (inline) |

**Key principle:** Only `Computed value` is passed as inline content. Everything else is a path — the subagent batch-loads them.

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Pass everything below this line as the subagent prompt.

---

**Output Path:** {output_path}
Write the full prompt you receive to this file.

**Computed Context (no file on disk):**
{computed_value}
This is inline content — it exists only in this prompt, not on disk. Note this in your analysis.

**Step 1: Batch-load all reference files.**

Run this single batch command to load all context:
```
python .claude/scripts/workflow_cli.py batch --commands '[
  "read {project_overview_path}",
  {analysis_doc_read_commands}
  {source_file_read_commands}
  {rule_file_read_commands}
]'
```

After loading, you have all context in your session. Use it for the verification report.

**Files to verify (paths only — you load them):**

| Category | Paths |
|----------|-------|
| Project overview | {project_overview_path} |
| Analysis docs | {analysis_doc_paths} |
| Source files | {source_file_paths} |
| Rule files | {rule_file_paths} |

**Step 2: Test hash command.**

```
python .claude/scripts/workflow_cli.py batch --commands '[
  {hash_commands}
]'
```

**Step 3: Write verification report.**

Assemble your report per your agent definition's output format.

---

## Output Format

```
## Status
**Result:** SUCCESS | PARTIAL | FAILURE
**Prompt Dump Path:** {output_path}

## Prompt Analysis
**Total sections received:** {N}
**Paths received (not content):** {N}
**Content embedded inline:** {N}
**Estimated tokens saved vs full-content approach:** {estimate}

## Batch Results

### Read Operations
| # | Path | Status | Content Fingerprint (first 80 chars) |
|---|------|--------|--------------------------------------|
| 1 | {path} | OK / FAIL | {first 80 chars...} |

### Hash Operations
| # | Path(s) | Status | Hash |
|---|---------|--------|------|
| 1 | {paths} | OK / FAIL | {hash} |

## Contract Verification
**Pattern used:** paths-not-content
**All paths accessible:** YES / NO (list failures)
**Batch command worked:** YES / NO
**Token doubling detected:** YES (list which content was embedded AND readable from disk) / NO

## Escalations
None | {issues found}
```

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: SUCCESS ∣ PARTIAL ∣ FAILURE | Quick pass/fail |
| `## Prompt Analysis` | Paths received, Content embedded, Tokens saved | Verify paths-not-content pattern worked |
| `## Batch Results` | Read/Hash tables | Verify subagent could load all files |
| `## Contract Verification` | All paths accessible, Token doubling detected | The key verification — did the new pattern work? |
| `## Escalations` | Issues | Any problems to fix |
