---
description: "Maintain the knowledge layer — component analysis docs, project overview, rules"
---

# /doc-update — Documentation Update

Maintain the knowledge layer after code changes. Handles component analysis docs, project overview, and rules.

**Input:**
- `/doc-update --plan-dir $PLAN_DIR` — post-execution reconciliation (full)
- `/doc-update {component-path}` — single component update
- `/doc-update` — auto-detect active plan, or ask for component path

## Step 0: Determine Mode

| Input | Mode | Action |
|---|---|---|
| `--plan-dir $PLAN_DIR` | Reconciliation | Proceed to Step 1 |
| Component path | Single | Skip to Step 2 with just this component |
| No args | Auto-detect | Use CLI `find-active` — if active plan found, use as $PLAN_DIR → reconciliation. If none, ask user for component path → single mode. |

## Step 1: Gather Data & Build Manifest (reconciliation mode only)

**1. Gather data:**

Already in conversation context (from execution):
- Plan summary
- Executor discoveries (from executor output `## Discoveries` sections)

New data needed:
- Use the CLI `state get execution_start_commit --plan-dir $PLAN_DIR` to get the start commit
- **Cumulative diff:** `git diff {start_commit}..HEAD --name-only`
- **Affected components:** derive from cumulative diff + phase files (deduplicate)

**2. Build Reconciliation Manifest:**

Analyze gathered data and ALL executor discoveries. Produce:

**Component Updates** — one row per affected component:

| Column | Content |
|---|---|
| Component | Component path |
| Changed Files | Files changed in cumulative diff for this component |
| Discoveries | Relevant discoveries (including cross-component), or "—" |

Cross-component discoveries go into EACH affected component's row.

**Project-Level Updates** — one row per project-wide finding (skip if none):

| Column | Content |
|---|---|
| Finding | What was discovered or changed |
| Target | `project-overview.md`, `rules/planning/`, or `rules/code/` |
| Proposed Update | Specific content to add or change |

Only non-trivial, repeatable findings not already captured at component level.

## Step 2: Prepare Components

For each component (from manifest in reconciliation mode, or the single component):
1. Check if `{component}.analysis.md` exists
2. **Exists** → add to assessment list
3. **Does NOT exist** → invoke `/analyze {component-path}` (full mode). DONE for this component.

## Step 3: Assess Change Significance

Read the prompt template: `.claude/skills/doc-update/doc-updater-prompt.md`

Collect shared data once (project overview, plan context) + per-component data for each component in assessment list. Fill the prompt template.

Spawn **one** doc-updater subagent (`.claude/agents/doc-updater.md`). It processes all components sequentially.

| Level | Meaning | Example | Action |
|-------|---------|---------|--------|
| **NO_UPDATE** | Docs still accurate | Typo fix, dependency bump | Skip |
| **MINOR_UPDATE** | Docs incomplete | New field, new endpoint | Patch inline |
| **MAJOR_UPDATE** | Docs misleading | Data flow changed, API broke | Full `/analyze` |

## Step 4: Handle Subagent Result

**Parse output** per `doc-updater-prompt.md` § "For Orchestrator — Expected Output":
- Read `## Status` → `**Result**` and `**Breakdown**` for quick summary
- For each component in `## Components`, read `**Classification**` and `**Escalation**`
- Read `## Escalations` table for all components needing `/analyze`

Route each component:

| Classification | Escalation | Action |
|---|---|---|
| `NO_UPDATE` | `NONE` | Skip |
| `MINOR_UPDATE` | `NONE` | Proceed to Step 5 |
| `MAJOR_UPDATE` | `ANALYZE_REQUIRED` | Invoke `/analyze` on the component (pass `**Discoveries to Pass**`) |

## Step 5: Verify

Per component with MINOR or MAJOR updates:
1. Confirm `.analysis.md` exists
2. Use CLI `analysis check` — verify `fresh`
3. Confirm frontmatter populated
4. If stale after MINOR: re-run CLI `hash` and patch `source_hash`

## Step 6: Process Project-Level Updates (reconciliation mode only)

For each row in Project-Level Updates:
- Present to user: "During execution, I discovered: {Finding}. Target: {Target}. Proposed update: {Proposed Update}"
- If user approves: apply the update
- If user declines: skip

## Constraints
- Do NOT re-analyze components classified as NO_UPDATE
- Do NOT do full rewrite for MINOR changes — patch inline
- Do NOT skip existence check (Step 2)
- Do NOT skip classification — always assess before acting
- In single mode (no plan context), assess based on diff alone
- MINOR patches update `source_hash` but skip `dependency_tree` hashes
