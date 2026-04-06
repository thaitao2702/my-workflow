---
description: |
  Maintain the knowledge layer after code changes — component analysis docs,
  project overview, and rules. Handles post-execution reconciliation (full
  pipeline with discoveries/decisions from state) and single-component updates.
  Use when the user wants to update docs after changes, reconcile analysis docs,
  refresh documentation, or says "update the docs" — even if they don't say
  "/doc-update." Also triggers after /execute completes (Step 3a) and when
  analysis docs are suspected stale.
  Do NOT use for initial analysis (use /analyze), plan creation (use /plan),
  or code implementation (use /execute).
---

# /doc-update — Documentation Update

Maintain the knowledge layer after code changes. Handles component analysis docs, project overview, and rules.

**Input:**
- `/doc-update --plan-dir $PLAN_DIR` — post-execution reconciliation (full)
- `/doc-update {component-path}` — single component update
- `/doc-update` — auto-detect active plan, or ask for component path

## Expert Vocabulary Payload

**Change Assessment:** significance classification (NO_UPDATE/MINOR_UPDATE/MAJOR_UPDATE), public API surface analysis, behavioral change detection, additive vs. breaking change, conservative classification principle (when uncertain, classify higher)

**Documentation Patching:** surgical patch, table row insertion, frontmatter field update (source_hash, last_analyzed), section-level preservation, minimum effective patch, Hidden Details table, Design Decisions table

**Knowledge Routing:** discovery routing (component field → manifest row), decision routing, cross-component discovery propagation, reconciliation manifest, cumulative diff analysis

**State Integration:** CLI-persisted discoveries (state get-discoveries), CLI-persisted decisions (state get-decisions), execution_start_commit, plan summary (plan get summary), context-compression-safe data

**Escalation:** ANALYZE_REQUIRED escalation, MAJOR_UPDATE trigger, full re-analysis delegation, discoveries-to-pass packaging

## Anti-Pattern Watchlist

### Full Rewrite on Minor Change
- **Detection:** MINOR_UPDATE classification produces a completely regenerated analysis doc. Multiple sections rewritten when only one table row was needed. Diff between old and patched doc shows changes far beyond what the code diff warrants.
- **Resolution:** For MINOR_UPDATE, only touch sections affected by the diff. Add rows, update fields, preserve everything else verbatim. If changing more than 3-4 sections, reassess whether this is actually MAJOR.

### Skipped Classification
- **Detection:** Doc-updater acts on components without reading the diff first. Reasoning bullets are generic ("code was updated") instead of traced to specific changes. Actions taken before classification is stated.
- **Resolution:** Always classify before acting. Every reasoning bullet must reference a specific line or hunk from the diff. If you cannot point to the diff, the reasoning is speculation.

### Discovery/Decision Drop
- **Detection:** State contains discoveries or decisions for a component, but the manifest row shows "—" for that component. Knowledge from execution is not routed to the doc-updater subagent.
- **Resolution:** Route every discovery/decision to the affected component's manifest row using the `component` field. Cross-component findings go into EACH affected row. Verify by checking state entries against manifest before spawning the subagent.

### Stale Hash After Patch
- **Detection:** Analysis doc is patched (rows added, fields updated) but `source_hash` is not recomputed or `last_analyzed` is not updated. Frontmatter metadata doesn't reflect the patch.
- **Resolution:** Every MINOR_UPDATE must update both `source_hash` (via CLI hash command) and `last_analyzed` (to today's date). These are mandatory — the freshness system breaks silently without them.

### Internal-as-Major Misclassification
- **Detection:** Internal refactoring (variable renames, code reorganization, log changes) classified as MAJOR_UPDATE. Reasoning references implementation details rather than public API or behavioral changes.
- **Resolution:** Ask: "Would someone using this component's public API notice the change?" If no → NO_UPDATE. Internal refactoring that preserves behavior does not make docs misleading. Over-classifying wastes tokens on unnecessary full re-analysis.

## Step 0: Determine Mode

| Input | Mode | Action |
|---|---|---|
| `--plan-dir $PLAN_DIR` | Reconciliation | Proceed to Step 1 |
| Component path | Single | Skip to Step 2 with just this component |
| No args | Auto-detect | Use CLI `find-active` — if active plan found, use as $PLAN_DIR → reconciliation. If none, ask user for component path → single mode. |

## Step 1: Gather Data & Build Manifest (reconciliation mode only)

**1. Gather data:**

From plan files:
- Plan summary: use CLI `plan get summary --plan-dir $PLAN_DIR`

From state (persisted during execution):
- Executor discoveries: use CLI `state get-discoveries --plan-dir $PLAN_DIR`
- Executor decisions: use CLI `state get-decisions --plan-dir $PLAN_DIR`

Other data needed:
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
| Decisions | Relevant decisions for this component, or "—" |

Cross-component discoveries and decisions go into EACH affected component's row. Route using the `component` field from each discovery/decision entry.

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
- Do NOT skip existence check (Step 2) — missing analysis docs need `/analyze`, not patching
- In single mode (no plan context), assess based on diff alone — apply more conservative classification
- MINOR patches update `source_hash` but skip `dependency_tree` hashes

## Questions This Skill Answers

- "Update the docs"
- "Reconcile analysis docs after execution"
- "/doc-update"
- "Refresh documentation after changes"
- "Update analysis docs for [component]"
- "Are the docs still accurate after my changes?"
- "Run doc update for the plan"
- "Update the knowledge layer"
- "Sync docs with code changes"
- "Check if analysis docs need updating"
- "Update docs for src/services/auth.ts"
- "/doc-update --plan-dir .workflow/plans/260328-feature"
