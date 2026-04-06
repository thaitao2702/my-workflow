---
description: |
  Apply an existing integration template to accelerate a new implementation.
  Collects variable values, resolves Guided sections with user input, and produces
  structured context that /plan consumes as enriched input. Use when the user wants
  to reuse a pattern, apply a template, follow a recipe, or says "do the same thing
  as last time but for [X]" — even if they don't say "/template-apply." Also
  triggers when /plan discovers a matching template during Step 2.
  Do NOT use for creating templates (use /template-create), direct implementation
  (use /execute), or ad-hoc planning without a template (use /plan directly).
---

# /template-apply — Apply Integration Template

Use an existing template to accelerate implementation of a new instance of a repeatable pattern.

**Input:** `/template-apply {name}` or invoked by `/plan` when a template match is found
**Output:** Structured template context that `/plan` consumes as enriched input

## Expert Vocabulary Payload

**Template Application:** variable collection, Guided section resolution ([G] elaboration), template context document, enriched plan input, pattern adaptation, reference file consultation

**Variable Resolution:** parametric substitution ([P] value replacement), guided elaboration ([G] user-directed adaptation), example-from-original, value prompting, fixed section passthrough ([F])

**Plan Integration:** template-to-plan handoff, quality review pass (via /plan), template discovery match (trigger keywords), plan enrichment, unresolved item resolution

## Anti-Pattern Watchlist

### Skipped Variable Collection
- **Detection:** Plan input generated without collecting all variable values first. Template context document contains `{unfilled_variable}` placeholders or example values from the original implementation instead of user-provided values.
- **Resolution:** Every variable in the template frontmatter must have a user-provided value before spawning the applier subagent. No defaults, no guessing from context.

### Plan Bypass
- **Detection:** Template output used directly for execution (/execute) without going through /plan for quality review and codebase adaptation. Template steps treated as a plan.
- **Resolution:** Templates are patterns, not plans. They always go through /plan for component intelligence gathering, plan design, and review. The template context document is INPUT to /plan, not a replacement for it.

### Template Modification
- **Detection:** The template file itself (.workflow/templates/{name}/template.md) is edited during application. Variable values written into the template instead of passed through.
- **Resolution:** Templates are shared artifacts — never modify them during application. Pass all customization through variables and guided section responses. The template stays generic for the next user.

### Ignored References
- **Detection:** Reference files in the template's references/ directory are not read or not passed to the applier subagent. The planner receives template steps without the annotated source patterns.
- **Resolution:** Reference files contain [F]/[P]/[G]-annotated code showing what to keep and what to change. Always read all reference files and include them in the subagent prompt.

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
- Do NOT modify the template file itself — it's a shared artifact for all future uses

## Questions This Skill Answers

- "Apply the payment template for PayPal"
- "Do the same thing we did for Stripe but for [X]"
- "/template-apply {name}"
- "Reuse the export template"
- "Use a template for this"
- "Apply the [pattern] recipe"
- "Do we have a template for this?"
- "Same pattern, different provider"
- "Follow the integration template"
- "Apply the CRUD template for orders"
- "Reuse what we built for users but for products"
