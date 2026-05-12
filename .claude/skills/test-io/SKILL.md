---
description: |
  Test the I/O contract between orchestrator and subagent. Verifies the
  "pass paths, not content" pattern by spawning a test-echo agent that
  records its prompt and batch-loads files from paths. Use to validate
  that the token-saving refactor works before applying it to real agents.
  Do NOT use in production — this is a diagnostic tool.
---

# /test-io — Verify Agent I/O Contract

You are testing the orchestrator→subagent I/O pattern. This skill collects PATHS (not file content), fills a prompt template with those paths, spawns a test agent that loads files itself, and verifies the results.

**Input:** `/test-io` (no arguments needed)
**Output:** Verification report showing whether the paths-not-content pattern works

## Step 1: Discover Test Files

Find real files in the project to use as test subjects. We need:
- Project overview: `.workflow/project-overview.md`
- 1-2 analysis docs: any `.analysis.md` files (use Glob to find them)
- 2-3 source files: any real source files in the project
- Rule files: `.claude/rules/quality-criteria.md` and `.claude/rules/tdd-policy.md`

If `.workflow/project-overview.md` doesn't exist, use `.claude/rules/agent-contracts.md` as a substitute.
If no `.analysis.md` files exist, skip that category.

**Collect PATHS only.** Do NOT read file contents.

## Step 2: Read Prompt Template

Read `.claude/skills/test-io/test-prompt.md`.

## Step 3: Fill Prompt Template

Fill the **For Subagent** section with collected PATHS:

- `{output_path}` → `.workflow/test-io-output/prompt-received.md`
- `{computed_value}` → `"This is a computed value: session_id=test-001, timestamp=now. It has no file on disk — only exists in this prompt."`
- `{project_overview_path}` → the path found in Step 1
- `{analysis_doc_paths}` → comma-separated list of paths, or `None`
- `{analysis_doc_read_commands}` → one `"read {path}",` line per analysis doc (for the batch command)
- `{source_file_paths}` → comma-separated list of paths
- `{source_file_read_commands}` → one `"read {path}",` line per source file
- `{rule_file_paths}` → comma-separated list of paths
- `{rule_file_read_commands}` → one `"read {path}",` line per rule file
- `{hash_commands}` → one `"hash {path}",` line per source file

**CRITICAL: Do NOT read any of these files.** The whole point is that you pass paths and the subagent reads them. If you read them here, you've doubled the tokens.

## Step 4: Spawn Test Agent

Spawn the test-echo agent (`.claude/agents/test-echo.md`) with `subagent_type: "coder"`, passing the filled **For Subagent** section as the prompt.

Run in foreground — we need the results immediately.

## Step 5: Verify Results

Parse the agent's response per `test-prompt.md` § "For Orchestrator — Expected Output":

1. Check `## Status` → `**Result**`
2. Check `## Contract Verification`:
   - **All paths accessible** should be YES
   - **Batch command worked** should be YES
   - **Token doubling detected** should be NO
3. Read the prompt dump file (`.workflow/test-io-output/prompt-received.md`) to verify the agent received paths, not content

Report results to the user:
- **PASS:** The paths-not-content pattern works. Safe to refactor real agents.
- **FAIL:** Show what went wrong. Which files couldn't be loaded? Did the batch command fail?

---CHECKPOINT---
Done: [Step 5 complete]
Next: [Report to user]
User directives: None
---END CHECKPOINT---
