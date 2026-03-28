---
description: "Extract a repeatable pattern from completed work into a reusable template"
---

# /template-create — Create Integration Template

Extract a repeatable implementation pattern from completed work. Captures steps, files, integration points, and marks what varies vs what stays fixed.

**Input:** `/template-create {name}`, `/template-create` (interactive selection), or invoked by `/plan` or `/execute` with `--from-session`
**Output:** `.workflow/templates/{name}/` directory with `template.md` and reference files

## Step 0: Determine Mode

### If invoked with `--from-session` (by `/plan` or `/execute`)
The calling skill passes rich session context (reasoning, decisions, discoveries). Skip to Step 1 Option A-session. The calling skill should also suggest a name — confirm with the user.

### If invoked with a name: `/template-create {name}`
Proceed to Step 0b (source selection).

### If invoked with no arguments: `/template-create`
Proceed to Step 0b (source selection). Ask for the name after the user has chosen their source.

### Step 0b: Source Selection

Present the menu immediately. **Do NOT scan plans, check git, or read any files yet** — just show the static options:

```
What would you like to create a template from?

[1] Current session context (from just-completed /plan or /execute)
    → Richest option — includes reasoning, decisions, and discoveries
[2] A completed plan/execution
    → I'll show you which plans are available
[3] Git branch or commit range
    → I'll use the diff to extract the pattern
[4] Specific files or component
    → Tell me which files to analyze
[5] Describe it manually
    → Tell me what pattern you want to capture
```

**After user selects:**

- **[1]** → Check if there's active session context from a recent `/plan` or `/execute` in this conversation. If yes: proceed to Step 1 Option A-session. If no (user selected this but no recent plan/execute in context): tell user "No recent plan/execute session found. Would you like to pick from completed plans instead?" → fall back to [2].
- **[2]** → NOW scan `.workflow/plans/` for completed plans. Show the list:
  ```
  Available completed plans:
  [a] 260325-payment-provider — "Add Stripe payment integration" (completed 2026-03-25)
  [b] 260320-user-export — "Add user data export feature" (completed 2026-03-20)
  ```
  After user picks a plan → proceed to Step 1 Option A-disk.
- **[3]** → Ask user: "Specify a git range (e.g., 'last 5 commits', 'abc123..def456') or use the current branch diff?" → proceed to Step 1 Option B.
- **[4]** → Ask user: "Which files or component path?" → proceed to Step 1 Option C.
- **[5]** → Ask user to describe the pattern → proceed to Step 1 Option D.

After source is determined, if no name was provided yet: ask for the template name.

## Step 1: Gather Source Material

### Option A-session: From current session (richest — invoked by `/plan` or `/execute`)

The calling skill passes context directly. You already have in the main session:
- **Plan reasoning** — why decisions were made, trade-offs considered
- **Component intelligence** — analysis findings that shaped the plan
- **Execution discoveries** — wrong assumptions, hidden behaviors found during implementation
- **Phase/task structure** — how the work was decomposed

Additionally gather from disk:
- **Git diff** — `git diff {execution_start_commit}..HEAD` for the concrete changes
- **Affected component `.analysis.md` files** — structured component knowledge

Pass ALL of this to the template-extractor agent in Step 2. This produces the richest templates because the agent gets both WHAT was built AND WHY.

### Option A-disk: From a completed execution (good — invoked later)

1. Look for plan directories in `.workflow/plans/` with `status: completed` in `state.json`
2. If found, present: "I see you completed **{plan-name}**. Create the template from this execution?"
3. If yes — load from disk using the CLI (see `.claude/scripts/workflow_cli.reference.md`):
   - **Plan intent:** read the plan summary
   - **What changed:** `git diff {execution_start_commit}..HEAD`
   - **Affected components:** read the full plan
   - **Component knowledge:** read `.analysis.md` files for all affected components
   - **Task structure:** read tasks for each phase

Less rich than session context (no reasoning/discoveries), but still strong source material.

### Option B: From git history

- **Git range:** "last 5 commits" or `abc123..def456`
- **Branch diff:** `git diff main..HEAD` for the current feature branch
- Run `git log` and `git diff` to extract changed files and diffs

### Option C: From existing code

- **File paths:** specific files that form the pattern
- **Component path:** a component path (will read its `.analysis.md` if available)
- Read current state of those files

### Option D: Mixed / Manual

Any combination of the above + verbal description from the user.

### For all options — also gather

- `.analysis.md` files for touched components (if they exist)
- Project overview — `.workflow/project-overview.md`

## Step 2: Pattern Extraction

Read the prompt template: `.claude/skills/template-create/template-extractor-prompt.md`

1. Collect each data item listed in **For Orchestrator** from its specified source (data varies by mode — collect what applies to the mode determined in Step 1)
2. Fill `{placeholders}` in **For Subagent** with collected data, include only sections that have data, keep purpose descriptions
3. Spawn a **template-extractor subagent** (`.claude/agents/template-extractor.md`), passing the filled **For Subagent** section as the prompt

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

## Step 3: Brief Review (user validates direction)

Before generating the full template, present a **brief summary** for user validation. The user understands the context better than the agent — they must confirm the direction before the full design.

Present:

```
Template: {name}
Pattern: {one-line description of what was abstracted}

Steps ({N} total):
  1. {step name} [{F|P|G}] — {one-line what it does}
  2. {step name} [{F|P|G}] — {one-line what it does}
  3. ...

Variables ({N} total):
  {var1} — {description} (example: {value})
  {var2} — {description} (example: {value})

Integration Points: {N} ({list of files/locations})
Gotchas: {N} captured

Does this look right? Anything missing, wrong, or that should be split/merged?
```

**Wait for user feedback.** The user may:
- Confirm → proceed to Step 4 (full design)
- Correct variability levels — "Step 3 should be [G] not [P], the UI varies a lot"
- Add missing steps — "You missed that we also need to update the navigation menu"
- Remove steps — "Step 5 is specific to Stripe, not part of the general pattern"
- Adjust variables — "Add {webhook_url} as a variable"
- Add gotchas — "Also, the admin cache must be invalidated after config change"

Incorporate feedback and re-present the brief if changes were significant. Only proceed when user confirms.

## Step 4: Full Template Design

After user approves the brief, generate the complete `template.md` + reference files with all details:
- Full step descriptions with file paths and instructions
- Complete variable table with descriptions and examples
- Integration points table with actions and variability levels
- Test requirements
- Annotated reference files with [F]/[P]/[G] markers
- All gotchas

Present the **full template** to the user for final review:
1. Show the complete template content
2. Ask: "Final review — anything to adjust before saving?"
3. User can still make adjustments at this stage
4. Iterate until user approves

## Step 5: Save Template

After user approves the full template:

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
