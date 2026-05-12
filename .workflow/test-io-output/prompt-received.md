You are a test echo agent. Read your agent definition first: `.claude/agents/test-echo.md`

Then follow the instructions below exactly.

---

**Output Path:** `.workflow/test-io-output/prompt-received.md`
Write the full prompt you receive to this file.

**Computed Context (no file on disk):**
This is a computed value: session_id=test-001, timestamp=2026-04-08T10:30:00Z. It has no file on disk — only exists in this prompt.
This is inline content — it exists only in this prompt, not on disk. Note this in your analysis.

**Step 1: Batch-load all reference files.**

Run this single batch command to load all context:
```
python .claude/scripts/workflow_cli.py batch --commands '["read .claude/rules/agent-contracts.md", "read .claude/scripts/workflow_cli.py", "read .claude/scripts/jira_fetch.py", "read .claude/rules/quality-criteria.md", "read .claude/rules/tdd-policy.md"]'
```

After loading, you have all context in your session. Use it for the verification report.

**Files to verify (paths only — you load them):**

| Category | Paths |
|----------|-------|
| Project overview (substitute) | `.claude/rules/agent-contracts.md` |
| Analysis docs | None |
| Source files | `.claude/scripts/workflow_cli.py`, `.claude/scripts/jira_fetch.py` |
| Rule files | `.claude/rules/quality-criteria.md`, `.claude/rules/tdd-policy.md` |

**Step 2: Test hash command.**

```
python .claude/scripts/workflow_cli.py batch --commands '["hash .claude/scripts/workflow_cli.py", "hash .claude/scripts/jira_fetch.py"]'
```

**Step 3: Write verification report.**

Assemble your report per your agent definition's output format.
