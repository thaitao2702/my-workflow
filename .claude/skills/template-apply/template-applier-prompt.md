# Template Applier Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect all before constructing the prompt.

| Data | Source |
|------|--------|
| Template content | `.workflow/templates/{name}/template.md` (full file) |
| Reference files | All files in `.workflow/templates/{name}/references/` |
| Variable values | Collected from user in SKILL.md Step 2 (one value per template variable) |
| Guided section answers | Collected from user in SKILL.md Step 2 (answers for each `[G]` section) |
| Project overview | `.workflow/project-overview.md` |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions. Pass everything below this line as the subagent prompt.

**Template Content:**
{template_content}
The template to apply. Contains steps with `[F]`/`[P]`/`[G]` variability markers, variables, integration points, and gotchas.

**Reference Files:**
{reference_files}
Annotated source snapshots from the original implementation. Each file has `[F]`/`[P]`/`[G]` markers showing what to keep vs change.

**Variable Values:**
{variable_values}
User-provided values for each `[P]` parametric variable. Substitute these exactly — no interpretation.

**Guided Section Answers:**
{guided_section_answers}
User-provided details for each `[G]` guided section. These describe how this instance differs from the original.

**Project Overview:**
{project_overview}
Codebase architecture and conventions. Use to ensure generated requirements fit existing patterns.

## Output Format

Follow this format exactly:

```
## Status
**Result:** SUCCESS | FAILURE
**Template:** {name}
**Requirements Generated:** {N}
**Variables Applied:** {N}
**Unresolved:** {N}

## Template Context Document

### Metadata
**Template:** {name}
**Source:** {original implementation reference from template frontmatter}
**Variables Applied:** {N}

### Requirements
| # | Name | Level | Source Step | Files | Criteria Count |
|---|------|-------|------------|-------|----------------|
| 1 | {name} | F ∣ P ∣ G | Step {N} | [{paths}] | {N} |

### Requirement Details
#### {N}. {name} [{F|P|G}]
**Source Step:** Step {N}: {step name}
**Description:** {concrete requirement with variable values substituted}
**Files:** [{target file paths}]
**Reference:** {pointer to reference file and section}
**Acceptance Criteria:**
- {verifiable criterion}

### Gotchas
| # | Gotcha | Scope | Source |
|---|--------|-------|--------|
| 1 | {finding} | pattern ∣ instance | {template step or reference} |

### Reference Context
{relevant annotated reference file excerpts that the planner/executor needs}

## Unresolved
| Type | Item | Detail |
|------|------|--------|
| missing_variable ∣ insufficient_guidance ∣ conflict | {variable or section name} | {what's needed from the user} |

## Escalations
| Type | Description |
|------|-------------|
| template_conflict ∣ convention_mismatch | {details of conflict with current codebase} |
```

- **Status.Result:** `SUCCESS` = all variables applied, all sections generated. `FAILURE` = critical unresolved items prevent generation.
- **Requirements:** Summary table first for quick scan, then one `####` detail block per requirement.
- **Requirement Level:** `F` = fixed (copy as-is), `P` = parametric (values substituted), `G` = guided (user-provided details shape the requirement).
- **Unresolved:** Items that need user input before `/plan` can proceed. Write "None" if all resolved.
- **Escalations:** Conflicts between the template pattern and current project conventions. Write "None" if no conflicts.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: SUCCESS ∣ FAILURE | Verify generation completed |
| | `**Unresolved**`: count | If > 0, ask user before proceeding to `/plan` |
| `## Template Context Document` | Full structured document | Pass entire section as enriched input to `/plan` |
| `## Unresolved` | Table: Type, Item, Detail | Present each to user for resolution. Type enum: `missing_variable`, `insufficient_guidance`, `conflict` |
| `## Escalations` | Table: Type, Description | Present to user. Type enum: `template_conflict`, `convention_mismatch` |
