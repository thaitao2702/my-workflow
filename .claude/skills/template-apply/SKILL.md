---
description: "Apply an integration template to accelerate a new implementation"
---

# /template-apply — Apply Integration Template

Use an existing template to accelerate implementation of a new instance of a repeatable pattern.

**Input:** `/template-apply {name}` or invoked by `/plan` when a template match is found
**Output:** Structured template context that `/plan` consumes as enriched input

## Step 1: Load Template

1. Read `.workflow/templates/{name}/template.md`
2. Read all files in `.workflow/templates/{name}/references/`
3. Present template overview to user:
   - Template name and description
   - Number of steps and their variability levels
   - Variables that need values

## Step 2: Collect Variables

For each variable defined in the template frontmatter:
1. Show: variable name, description, example from original
2. Ask user for the value

For `[G]` guided sections:
1. Show: what the original implementation did and why
2. Ask: "How should this differ for your case?"
   - e.g., "What fields does PayPal require on the settings page?"
   - e.g., "What columns should this table display?"

Collect all values before proceeding.

## Step 3: Generate Plan Input

Template-apply always produces structured input for `/plan`. Templates are patterns, not plans — they still need adaptation to the current codebase state and quality review before execution.

Read the prompt template: `.claude/skills/template-apply/template-applier-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source
2. Fill `{placeholders}` in **For Subagent** with collected data, keep purpose descriptions
3. Spawn a **template-applier subagent** (`.claude/agents/template-applier.md`), passing the filled **For Subagent** section as the prompt

**Parse applier output** per `template-applier-prompt.md` § "For Orchestrator — Expected Output":
- Read `## Status` → `**Result**` and `**Unresolved**` count
- If `**Unresolved**` > 0: read `## Unresolved` table, present each item to user for resolution, then re-run
- Extract `## Template Context Document` → this is the enriched input for `/plan`
- Read `## Escalations` → present any template-project conflicts to user

4. Hand off to `/plan`:
   - If invoked by `/plan` (template discovery): return the `## Template Context Document` section. The planner uses it as enriched input — it replaces the requirements gathering phase but the planner still does component intelligence, plan design, review, and approval.
   - If invoked directly: use the Skill tool to invoke `/plan` with the `## Template Context Document` as the requirements input.

## Constraints
- Do NOT skip variable collection — every variable must have a value before generating output
- Do NOT bypass `/plan` — templates always go through planning for quality review and adaptation
- Do NOT ignore reference files — they contain the annotated patterns the planner and executor need
- Do NOT modify the template itself — it's a shared artifact
