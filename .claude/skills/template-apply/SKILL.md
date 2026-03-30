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

1. Transform template steps into a **template context document**:
   - `[F]` fixed steps → concrete requirements with exact instructions
   - `[P]` parametric steps → concrete requirements with variable values substituted
   - `[G]` guided steps → requirements with user-provided details + reference to original implementation
2. Include in the document:
   - **Template name and source** — so the planner knows this is template-driven
   - **Requirements list** — one requirement per template step, with variable values filled in
   - **Reference files** — annotated code from `.workflow/templates/{name}/references/` that shows the pattern
   - **Gotchas** — known edge cases and lessons learned from the template
   - **Guided section answers** — user's answers for `[G]` sections (from Step 2)
3. Hand off to `/plan`:
   - If invoked by `/plan` (template discovery): return the template context document. The planner uses it as enriched input — it replaces the requirements gathering phase but the planner still does component intelligence, plan design, review, and approval.
   - If invoked directly: use the Skill tool to invoke `/plan` with the template context document as the requirements input.

## Constraints
- Do NOT skip variable collection — every variable must have a value before generating output
- Do NOT bypass `/plan` — templates always go through planning for quality review and adaptation
- Do NOT ignore reference files — they contain the annotated patterns the planner and executor need
- Do NOT modify the template itself — it's a shared artifact
