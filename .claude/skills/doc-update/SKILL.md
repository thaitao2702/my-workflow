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

Read the prompt template: `.claude/skills/doc-update/doc-updater-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions
3. Spawn a **doc-updater subagent** (`.claude/agents/doc-updater.md`), passing the filled **For Subagent** section as the prompt

The agent classifies the changes:

| Level | Meaning | Example | Action |
|-------|---------|---------|--------|
| **NO UPDATE** | Trivial change, docs still accurate | Typo fix, log message, dependency bump | Skip — do nothing |
| **MINOR UPDATE** | Additive change, existing docs mostly accurate | New field, new prop, new endpoint added | Patch `.analysis.md` inline |
| **MAJOR UPDATE** | Structural change, docs are now misleading | Data flow changed, API contract changed, refactored | Trigger full `/analyze` |

## Step 2: Handle Subagent Result

The subagent returns its classification and any actions it took. The orchestrator acts based on the result:

| Classification | What the subagent did | What the orchestrator does next |
|---|---|---|
| **NO UPDATE** | Reported classification only | Nothing — proceed to next component |
| **MINOR UPDATE** | Already patched `.analysis.md` inline (added rows, updated hash/frontmatter) | Proceed to Step 3 (verify the patch) |
| **MAJOR UPDATE** | Reported classification and recommended `/analyze` | Use the Skill tool to invoke `/analyze` on the component path |

## Step 3: Verify

After any update (MINOR or MAJOR):
1. Confirm `.analysis.md` exists
2. Read frontmatter: verify `source_hash` matches current file hash (use CLI `hash` command with the component's `entry_files`)
3. Confirm `name`, `type`, `summary`, `entry_files` are populated
4. If hash mismatch after MINOR update: the doc-updater may not have computed the hash correctly — re-run the hash and patch the frontmatter

## Constraints
- Do NOT re-analyze components classified as NO UPDATE — that wastes tokens
- Do NOT do a full rewrite for MINOR changes — patch inline
- Do NOT skip Step 0 — always check if the analysis doc exists before assessing
- Do NOT skip the assessment step — always classify before acting
- When no plan context is available (manual invocation), assess based on the diff alone
- MINOR patches update `source_hash` but intentionally skip `dependency_tree` hashes — recomputing transitive dependency hashes adds complexity for little benefit. If a dependency changed, the next staleness check will detect the mismatch and trigger a full `/analyze`, which self-corrects.
