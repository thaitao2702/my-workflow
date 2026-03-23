---
description: "Assess change significance and update component documentation"
---

# /doc-update — Documentation Update

Assess whether code changes warrant documentation updates, then apply the appropriate level of update.

**Input:** List of affected component paths + git diff (provided by calling skill)
**Called by:** `/execute` after each phase, or manually

## Step 1: Assess Change Significance

Use the Agent tool to spawn a subagent with `.claude/agents/doc-updater.md`.

Provide:
1. **Git diff** for the changed files
2. **Existing `.analysis.md`** files for affected components
3. **Project overview** — `.workflow/project-overview.md`

The agent classifies each affected component's changes into one of three levels:

| Level | Meaning | Example | Action |
|-------|---------|---------|--------|
| **NO UPDATE** | Trivial change, docs still accurate | Typo fix, log message, dependency bump | Skip — do nothing |
| **MINOR UPDATE** | Additive change, existing docs mostly accurate | New field, new prop, new endpoint added | Patch `.analysis.md` inline |
| **MAJOR UPDATE** | Structural change, docs are now misleading | Data flow changed, API contract changed, refactored | Trigger full `/analyze` |

**Why Sonnet for assessment:** This step requires judgment — distinguishing "added a column" from "changed the data flow." Sonnet's judgment saves money: most changes are NO UPDATE or MINOR, avoiding unnecessary full rewrites.

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
- This triggers a full or update-mode re-analysis depending on the scope of changes

## Step 3: Project Overview Check

If any component was classified as MAJOR UPDATE:
- Check if the changes affect the project's overall architecture or module structure
- If yes: update `.workflow/project-overview.md` with the changes
- If no: skip

## Constraints
- Do NOT re-analyze components classified as NO UPDATE — that wastes tokens
- Do NOT do a full rewrite for MINOR changes — patch inline
- Do NOT skip the assessment step — always classify before acting
