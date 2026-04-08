## Agent I/O Contracts

All agent interactions (main agent ↔ subagent) follow typed contracts defined in prompt templates.

### Spawning an Agent

When spawning any subagent:
1. Read its prompt template (see reference table below)
2. Collect all data items listed in **"For Orchestrator — Data to Collect"** — the Data column uses the exact `{placeholder}` name from the subagent prompt
3. Fill `{placeholders}` in **"For Subagent — Prompt to Pass"** with the collected values
4. Pass the filled "For Subagent" section as the agent's prompt

**Placeholder format conventions — all values are raw strings:**
- **Single path:** `path/to/file.md` — raw string, no backtick wrapping
- **Path list:** `path/one.md, path/two.md, path/three.md` — comma-separated raw strings
- **Content (inline):** raw text, no wrapping — for computed values only
- **None/empty:** the literal string `None`

**Template rule:** Placeholders in the "For Subagent" section must be bare — no surrounding backticks in the template markup. Values are raw; templates position them.

### Parsing Agent Output

When receiving a subagent response:
1. Read `## Status` first — check `**Result**` for the outcome enum
2. Process agent-specific sections per **"For Orchestrator — Expected Output"** in the prompt template
3. Read `## Escalations` last — handle any items before proceeding

### Output Envelope (all agents)

Every agent response follows this structure:

```
## Status
**Result:** {enum — defined per agent}
{agent-specific typed status fields}

{agent-specific sections — typed fields and tables}

## Escalations
{typed table, or "None"}
```

Rules:
- `## Status` is always FIRST, `## Escalations` is always LAST
- All fields are named: `**FieldName:** value` — no unnamed free-text lines
- Arrays of typed objects use tables with named columns — no free-text bullet lists
- Enum values are exact strings (`SUCCESS` not "succeeded", `FAIL` not "failed")
- Empty sections keep the header with "None" — never omit a section

### Prompt Template Structure

Every prompt template has three sections:

| Section | Purpose | Audience |
|---------|---------|----------|
| **For Orchestrator — Data to Collect** | Input contract: what data to gather and from where | Orchestrator (SKILL.md) |
| **For Subagent — Prompt to Pass** | The prompt sent to the agent, including output format | Agent |
| **For Orchestrator — Expected Output** | Output parsing guide: field names, types, enums | Orchestrator (SKILL.md) |

### Efficient Data Loading (All Agents)

**Parallel tool calls.** When you need 3+ independent pieces of information (file reads, grep searches, etc.), issue all independent tool calls in parallel within a single response — not one at a time. This applies to native tools (Read, Grep, Glob) and CLI commands alike.

**CLI `batch` command.** For CLI-specific operations (read, hash, analysis check, grep), combine 3+ calls into one `batch` invocation. See `.claude/scripts/workflow_cli.reference.md` → "Batch Operations" for syntax.

**Paths, not content.** Prompt templates pass file paths to subagents — subagents load files themselves. Only computed values that don't exist on disk (git diffs, plan JSON extracts, session context, user directives) are passed as inline content in the prompt. This prevents token doubling.

### Agent → Prompt Template Reference

| Agent | Prompt Template |
|-------|----------------|
| executor | `.claude/skills/execute/executor-prompt.md` |
| reviewer (code) | `.claude/skills/execute/reviewer-prompt.md` |
| plan-reviewer | `.claude/skills/plan/plan-reviewer-prompt.md` |
| analyzer | `.claude/skills/analyze/analyzer-prompt.md` |
| doc-updater | `.claude/skills/doc-update/doc-updater-prompt.md` |
| template-extractor | `.claude/skills/template-create/template-extractor-prompt.md` |
| template-applier | `.claude/skills/template-apply/template-applier-prompt.md` |
| dependency-resolver | `.claude/skills/analyze/dependency-resolver-prompt.md` |
| acceptance-verifier | `.claude/skills/execute/acceptance-verifier-prompt.md` |
