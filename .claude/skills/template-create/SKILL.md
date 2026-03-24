---
description: "Extract a repeatable pattern from completed work into a reusable template"
---

# /template-create — Create Integration Template

Extract a repeatable implementation pattern from completed work. Captures steps, files, integration points, and marks what varies vs what stays fixed.

**Input:** `/template-create {name}`
**Output:** `.workflow/templates/{name}/` directory with `template.md` and reference files

## Step 1: Gather Source Material

### Option A: From a completed execution (richest source)

Check if there's a recently completed plan:

1. Look for plan directories in `.workflow/plans/` with `status: completed` in `state.json`
2. If found, present: "I see you completed **{plan-name}**. Create the template from this execution?"
3. If yes — auto-load everything from the execution context:
   - **Plan intent:** run `python .claude/scripts/workflow_cli.py plan get summary` — why it was built
   - **What changed:** `git diff {execution_start_commit}..HEAD` — the full implementation diff
   - **Affected components:** read from phase files via `python .claude/scripts/workflow_cli.py plan get` — which components were touched
   - **Component knowledge:** read `.analysis.md` files for all affected components — hidden details, integration patterns, architecture
   - **Task structure:** run `python .claude/scripts/workflow_cli.py phase tasks {N}` for each phase — how the work was broken down (this often maps directly to template steps)

This is the richest source because you have: what was built (diff), why (plan summary), how it was structured (phases/tasks), and deep component knowledge (analysis docs).

### Option B: From git history

If no completed execution or user prefers:
- **Git range:** "last 5 commits" or `abc123..def456`
- **Branch diff:** `git diff main..HEAD` for the current feature branch
- Run `git log` and `git diff` to extract changed files and diffs

### Option C: From existing code

- **File paths:** specific files that form the pattern
- **Component path:** a component path (will read its `.analysis.md` if available)
- Read current state of those files

### Option D: Mixed

Any combination of the above + verbal description from the user.

### For all options — also gather

- `.analysis.md` files for touched components (if they exist) — hidden details and integration patterns the raw diff doesn't show
- Project overview — `.workflow/project-overview.md` — architectural context

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

The agent uses multi-case reasoning internally to find the right abstraction level — it imagines other scenarios that would use this pattern to determine what's truly fixed vs parametric vs guided.

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
