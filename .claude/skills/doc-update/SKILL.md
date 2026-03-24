---
description: "Assess change significance and update component documentation"
---

# /doc-update — Documentation Update

Assess whether code changes warrant documentation updates, then apply the appropriate level of update. Handles both existing analysis docs and components that have never been analyzed.

**Input:** Component path + git diff + optional plan context (provided by calling skill)
**Called by:** `/execute` Step 3 (final reconciliation), or manually

## Step 0: Check Analysis Doc Exists

Before assessing significance, check if `{component}.analysis.md` exists alongside the source:

1. **Exists** → proceed to Step 1 (normal assessment flow)
2. **Does NOT exist** → this component has never been analyzed. Two sub-cases:
   - **Component was created during this execution** (didn't exist at `execution_start_commit`):
     → This is a brand new component. Use the Skill tool to invoke `/analyze {component-path}` (full mode). Skip Step 1-2 — full analysis covers everything.
   - **Component existed before but was never analyzed:**
     → Use the Skill tool to invoke `/analyze {component-path}` (full mode). This fills the gap that planning missed. Skip Step 1-2.

In both cases, after `/analyze` completes, verify the `.analysis.md` was created (artifact check), then DONE for this component.

## Step 1: Assess Change Significance

Use the Agent tool to spawn a subagent with `.claude/agents/doc-updater.md`.

Provide:
1. **Git diff** for the component's files
2. **Existing `.analysis.md`** file (full content)
3. **Project overview** — `.workflow/project-overview.md`
4. **Plan context** (if available) — what was being built and why. This helps the agent assess significance: "a field was added" is ambiguous, but "a field was added as part of the export feature" clarifies intent.

The agent classifies the changes:

| Level | Meaning | Example | Action |
|-------|---------|---------|--------|
| **NO UPDATE** | Trivial change, docs still accurate | Typo fix, log message, dependency bump | Skip — do nothing |
| **MINOR UPDATE** | Additive change, existing docs mostly accurate | New field, new prop, new endpoint added | Patch `.analysis.md` inline |
| **MAJOR UPDATE** | Structural change, docs are now misleading | Data flow changed, API contract changed, refactored | Trigger full `/analyze` |

## Step 2: Apply Updates

Based on the agent's classification:

### NO UPDATE
- Do nothing. Cost: ~500 tokens (just the assessment).

### MINOR UPDATE
- The doc-updater agent patches the existing `.analysis.md` inline:
  - Add new props/fields to tables
  - Add new dependency entries
  - Update summary if needed
  - Update `last_commit` and `last_analyzed` in frontmatter

### MAJOR UPDATE
- Use the Skill tool to invoke `/analyze` on the component path
- This triggers update-mode or full-mode analysis depending on the scope of changes

## Step 3: Verify

After any update (MINOR or MAJOR):
1. Confirm `.analysis.md` exists and has current `last_commit`
2. Confirm frontmatter fields are populated

## Constraints
- Do NOT re-analyze components classified as NO UPDATE — that wastes tokens
- Do NOT do a full rewrite for MINOR changes — patch inline
- Do NOT skip Step 0 — always check if the analysis doc exists before assessing
- Do NOT skip the assessment step — always classify before acting
- When no plan context is available (manual invocation), assess based on the diff alone
