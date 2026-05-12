---
description: |
  Test the placeholder passing flow between the /plan skill (Step 8) and the
  plan-reviewer subagent. Mirrors the exact placeholder structure of
  plan-reviewer-prompt.md, spawns a test echo agent, and verifies that
  placeholders are filled and received correctly. Diagnostic tool only.
  Do NOT use in production — this validates the orchestrator→subagent
  I/O contract for the plan review step.
---

# /test-plan-review — Verify Plan Review Placeholder Passing

You are testing the /plan skill's Step 8 (Automated Review) placeholder flow. This skill collects the same placeholder types as the plan SKILL.md would, fills the same template structure as plan-reviewer-prompt.md, and spawns a test agent that echoes back what it received — reporting all values through Escalations.

**Input:** `/test-plan-review` (no arguments needed)
**Output:** Verification report showing whether placeholders pass correctly from orchestrator to subagent

## Step 1: Collect Test Data

Collect real paths for each placeholder — same data items that /plan Step 8 would collect:

| Placeholder | How to collect |
|-------------|---------------|
| `{$PLAN_DIR}` | Find any existing plan: `ls .workflow/plans/`. Use the first one. If none, create a dummy: `.workflow/plans/test-placeholder-check` |
| `{planning_rules_dir}` | Check if `.workflow/rules/planning/` exists. If yes, use the path. If not, use `None`. |
| `{component_doc_paths}` | Glob for `**/*.analysis.md`. If found, use comma-separated paths. If none, use `None`. |
| `{source_file_paths}` | Use 2 real files: `.claude/scripts/workflow_cli.py`, `.claude/rules/agent-contracts.md` |
| `{project_overview_path}` | If `.workflow/project-overview.md` exists, use it. Otherwise use `.claude/rules/agent-contracts.md` as substitute. |
| `{output_path}` | `.workflow/test-plan-review-output/prompt-received.md` |

Record the exact value for each — you will compare these against what the subagent reports.

## Step 2: Read Prompt Template

Read `.claude/skills/test-plan-review/test-plan-review-prompt.md`.

## Step 3: Fill Prompt Template

Fill the **For Subagent** section using agent-contracts.md placeholder format conventions:
- **Single path:** backtick-wrapped — `` `path/to/file.md` ``
- **Path list:** comma-separated, each backtick-wrapped — `` `path/one.md`, `path/two.md` ``
- **None/empty:** the literal string `None`

Extract the content after the `---` divider in the "For Subagent" section. Replace all `{placeholders}` with collected values.

**NOTE:** This is the step under test. The agent-contracts convention says single paths should be backtick-wrapped. But the template ALSO wraps some placeholders in backticks. The test reveals whether this causes double wrapping.

## Step 4: Spawn Test Agent

Spawn the test-plan-review-echo agent (`.claude/agents/test-plan-review-echo.md`) with `subagent_type: "coder"`, passing the filled **For Subagent** section as the prompt.

Run in **foreground** — we need results immediately.

## Step 5: Verify Results

Parse the agent's response per the prompt template's "For Orchestrator — Expected Output":

1. Check `## Status` → `**Result**` should be `ECHO_COMPLETE`
2. Check `## Placeholder Values` table — compare each "Received Value" against what you sent in Step 3
3. Check `## Format Analysis`:
   - **Header/CLI consistency** should be MATCH
   - **Double wrapping detected** should be NO
4. Check `## Escalations` — these are the primary findings

Optionally read the prompt dump file at `{output_path}` to verify the raw prompt.

**Report to user:**

| Check | Expected | Finding |
|-------|----------|---------|
| $PLAN_DIR header value | correct path | {what agent received} |
| $PLAN_DIR CLI value | same as header, no backticks in command | {what agent received} |
| component_doc_paths | correct paths or None | {what agent received} |
| source_file_paths | correct paths | {what agent received} |
| project_overview_path | correct path, single backtick wrap | {what agent received} |
| planning_rules_dir | correct path or None | {what agent received} |
| Double wrapping anywhere? | NO | {finding} |
| Header/CLI match? | YES | {finding} |

**Conclusion:** State whether the agent-contracts placeholder convention works correctly with the plan-reviewer-prompt.md template design. If not, recommend whether to fix the convention or the template.
