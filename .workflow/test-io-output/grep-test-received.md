You are a test echo agent. Read your agent definition: `.claude/agents/test-echo.md`

Your task is to verify that **batch grep** works correctly from a subagent. This simulates the plan-reviewer's codebase alignment check (dimension 10) where it needs to verify multiple patterns exist in the codebase.

---

**Output Path:** `.workflow/test-io-output/grep-test-received.md`
Write the full prompt you receive to this file.

**Scenario:** You are a plan reviewer verifying codebase alignment. The plan references these classes/functions/patterns that should exist in the codebase. You need to verify all of them.

**Step 1: Batch grep — verify multiple patterns in one call.**

Run this single batch command to search for all patterns at once:
```
python .claude/scripts/workflow_cli.py batch --commands '["grep --path .claude/scripts --type py def cmd_grep", "grep --path .claude/scripts --type py def cmd_read", "grep --path .claude/scripts --type py def dispatch", "grep --path .claude/rules --context 2 Batch Command Usage", "grep --path .claude/agents Anti-Pattern Watchlist"]'
```

**Step 2: Batch grep — patterns that should NOT match (negative test).**

```
python .claude/scripts/workflow_cli.py batch --commands '["grep --path .claude/scripts --type py class NonExistentClass", "grep --path .claude/rules ThisPatternDoesNotExist12345"]'
```

**Step 3: Mixed batch — combine read + grep in a single call.**

This tests that agents can mix operation types in one batch:
```
python .claude/scripts/workflow_cli.py batch --commands '["read .claude/rules/tdd-policy.md", "grep --path .claude/scripts --type py def cmd_batch", "hash .claude/rules/tdd-policy.md"]'
```

**Step 4: Write verification report.**

Use this format:

```
## Status
**Result:** SUCCESS | PARTIAL | FAILURE

## Batch Grep Results

### Step 1: Positive Pattern Matches (5 patterns)
| # | Pattern | Search Path | Status | Match Count | First Match (file:line) |
|---|---------|-------------|--------|-------------|------------------------|

### Step 2: Negative Pattern Matches (2 patterns — expect no matches)
| # | Pattern | Search Path | Status | Expected | Actual |
|---|---------|-------------|--------|----------|--------|

### Step 3: Mixed Batch (read + grep + hash)
| # | Command Type | Target | Status | Fingerprint |
|---|-------------|--------|--------|-------------|

## Contract Verification
**Batch grep works:** YES / NO
**No-match handled gracefully:** YES / NO (did it error or return "(no matches)"?)
**Mixed batch works:** YES / NO
**Total batch calls made:** {N} (should be 3, not 5+7=12 individual calls)

## Escalations
None | {issues found}
```
