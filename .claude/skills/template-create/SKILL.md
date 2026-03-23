---
description: "Extract a repeatable pattern from completed work into a reusable template"
---

# /template-create — Create Integration Template

Extract a repeatable implementation pattern from completed work. Captures steps, files, integration points, and marks what varies vs what stays fixed.

**Input:** `/template-create {name}`
**Output:** `.workflow/templates/{name}/` directory with `template.md` and reference files

## Step 1: Gather Source Material

Ask the user: **"What work should I analyze to create this template?"**

Offer options:
- **Git range:** "last 5 commits" or a commit range like `abc123..def456`
- **File paths:** specific files that form the pattern
- **Existing component:** a component path (will read its `.analysis.md` if available)
- **Mixed:** any combination + verbal description of intent

Based on user's answer:
- Git range → run `git log` and `git diff` to extract changed files and diffs
- File paths → read current state of those files
- Component path → read component source + its `.analysis.md` if it exists

## Step 2: Pattern Extraction

Spawn a subagent with `.claude/agents/template-extractor.md`.

Provide:
1. **All source material** (files, diffs, analysis docs)
2. **Template name** from user input
3. **Project overview** — `.workflow/project-overview.md`

The agent analyzes the source and identifies:
- **The repeatable pattern** — the "shape" of the work
- **Steps** — ordered sequence of file operations
- **Variability per step:**
  - `[F]` Fixed — copy as-is every time
  - `[P]` Parametric — same structure, swap values
  - `[G]` Guided — follow the shape but expect structural differences
- **Variables** — names/values that change each instance
- **Integration points** — where new code connects to existing code
- **Test patterns** — what tests follow the pattern
- **Gotchas** — non-obvious things learned during the original work

The agent produces: `template.md` content + reference file contents.

## Step 3: User Review

Present the generated template to the user:

1. Show the template overview: steps, variables, variability levels
2. Ask the user to review and adjust:
   - Adjust variability levels (promote `[P]` to `[G]` or demote to `[F]`)
   - Add/remove variables
   - Add gotchas the AI missed
   - Refine step descriptions
3. Iterate until user approves

## Step 4: Save Template

1. Create directory: `.workflow/templates/{name}/`
2. Write `template.md` with full structure (YAML frontmatter + body)
3. Create `references/` subdirectory
4. Write reference files (annotated snapshots of key source files)
5. Update `.workflow/templates/index.md` — add a row to the table:
   ```
   | {name} | {pattern description} | {trigger keywords} | {source} ({date}) |
   ```

## Template File Format

```markdown
---
name: {template-name}
description: {one-line description}
created_from: {source description}
created_at: {YYYY-MM-DD}
trigger_keywords: [{keywords for auto-discovery}]
variables:
  - name: {var}
    description: {what it represents}
    example: {value from original}
---

# {Template Name}

## Overview
{1-2 sentences — what this pattern does and when to use it}

## Variables
| Variable | Description | Example (from original) |
|----------|-------------|------------------------|
| `{var}` | ... | ... |

## Steps

### Step 1: {name} [F|P|G]
**Files:** {file paths, with variables}
**Reference:** [references/{slug}.md](references/{slug}.md)
**What to do:**
- {instructions}

## Integration Points
| Integration Point | File | Action | Level |
|-------------------|------|--------|-------|
| ... | ... | ... | [F|P|G] |

## Tests Required
| Test | File Pattern | Level | Notes |
|------|-------------|-------|-------|
| ... | ... | [F|P|G] | ... |

## Gotchas & Lessons Learned
- {non-obvious finding}
```

## Reference File Format

```markdown
---
source: {original file path}
snapshot_commit: {git hash}
---

# {FileName} — Reference for {Template Name}

## Key Structure
{Annotated code with [F], [P], [G] markers in comments}

## What to Keep
- {patterns that must stay the same}

## What to Change
- {parts that vary per instance}
```

## Constraints
- Do NOT create templates from work that isn't actually repeatable
- Do NOT include raw code dumps in reference files — annotate with [F]/[P]/[G] markers
- Do NOT skip the user review step — templates are a shared artifact
- Do NOT forget to update the index file
