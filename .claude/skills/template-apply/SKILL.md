---
description: "Apply an integration template to accelerate a new implementation"
---

# /template-apply — Apply Integration Template

Use an existing template to accelerate implementation of a new instance of a repeatable pattern.

**Input:** `/template-apply {name}` or invoked by `/plan` when a template match is found
**Output:** A plan skeleton or task list, ready for `/plan` or `/execute`

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

## Step 3: Generate Output

Ask the user: **"Generate a plan for `/plan`, or execute directly?"**

### Option A: Generate Plan (recommended if any `[G]` sections exist)

1. Transform template steps into plan phases/tasks:
   - `[F]` steps → concrete tasks with exact instructions
   - `[P]` steps → concrete tasks with variable values substituted
   - `[G]` steps → tasks with user-provided details + reference to original
2. Include reference files as context for the planner
3. Return the plan skeleton to the calling context:
   - If invoked by `/plan`: return as template context for the planner agent
   - If invoked directly: use the Skill tool to invoke `/plan` with the generated context

### Option B: Execute Directly (only if ALL sections are `[F]` or `[P]`)

1. Check: are there any `[G]` sections?
   - **If yes:** warn the user: "This template has guided sections that need planning. Recommend going through `/plan` first."
   - If user insists: proceed but flag `[G]` sections for human review during execution
2. Generate `/execute`-compatible task list with:
   - All variable values substituted
   - Reference files as context
   - Acceptance criteria derived from the template
3. Hand off to `/execute`

## Constraints
- Do NOT skip variable collection — every variable must have a value before generating output
- Do NOT auto-execute templates with `[G]` sections without warning
- Do NOT ignore reference files — they contain the annotated patterns the executor needs
- Do NOT modify the template itself — it's a shared artifact
