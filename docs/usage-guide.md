# AI Coding Workflow — Usage Guide

## Quick Start

1. Copy `.claude/` and `.workflow/` directories into your project root
2. Copy `CLAUDE.md` to your project root
3. Edit `.workflow/config.json` — set `project_name` and any project-specific settings
4. Run `/init` to generate your project overview
5. Start working: `/plan` → `/execute`

## Commands

### `/init` — Initialize Project

```
/init
```

Scans your project and generates `.workflow/project-overview.md` — a concise overview loaded on every session. Run once on a new project, or again after major structural changes.

**What it does:** Detects project type, reads configs/entry points, identifies architecture patterns, produces overview with Mermaid diagrams.

### `/plan` — Create Execution Plan

```
/plan "Add user export feature"
/plan ./requirements/export.md
/plan gh:123
/plan jira:PROJ-456
```

Transforms requirements into a phased, dependency-aware plan with automated quality review.

**Flow:**
1. Parse requirements from text, file, GitHub issue, or Jira ticket
2. Check for matching templates (auto-discovery)
3. Clarify ambiguities with you (max 3 rounds)
4. Analyze affected components (triggers `/analyze` if docs are stale/missing)
5. Generate phased plan with dependency graph
6. Automated 8-dimension review
7. Present for your approval

**Output:** `.workflow/plans/{date}-{name}/` with `plan.md`, phase files, `state.md`

### `/execute` — Execute Plan

```
/execute                    # Execute latest approved plan
/execute {plan-path}        # Execute specific plan
/execute --resume           # Resume interrupted execution
```

Implements the plan phase-by-phase with TDD, code review, and doc updates.

**Per task:** Write tests → implement → run tests → update state
**Per phase:** Code review → Playwright check (if UI) → doc updates → regression tests
**After all phases:** Final reconciliation, full test suite, execution summary

### `/analyze` — Component Analysis

```
/analyze src/services/authService.ts
/analyze src/modules/auth --recursive
```

Deep-analyzes a component and produces `{Component}.analysis.md` co-located with the source.

**Modes:**
- **Full** — complete analysis from scratch (Opus)
- **Update** — incremental update for changed code (Sonnet, auto-detected)
- **Recursive** — component + all its dependencies, leaf-to-top

**Staleness:** Automatically detected via `last_commit` in frontmatter vs git log. No manual tracking needed.

### `/template-create` — Extract Pattern

```
/template-create payment-provider
```

Extracts a repeatable pattern from completed work into a reusable template.

**Process:** Asks what to analyze (git range, files, or component) → extracts pattern with variability markers → you review → saved to `.workflow/templates/`

**Variability markers:**
- `[F]` Fixed — identical every time
- `[P]` Parametric — same structure, swap values
- `[G]` Guided — follow shape, expect differences

### `/template-apply` — Use Template

```
/template-apply payment-provider
```

Applies a template to accelerate a new implementation. Collects variable values, then generates a plan or task list.

**Auto-discovery:** When you run `/plan`, it automatically checks templates and suggests matches.

### `/doc-update` — Update Documentation

```
/doc-update
```

Assesses change significance for affected components and applies the right level of update. Usually called automatically by `/execute`, but can be run manually.

**Levels:** NO UPDATE (skip) → MINOR (patch inline) → MAJOR (trigger `/analyze`)

### `/jira` — Fetch Jira Ticket

```
/jira PROJ-456
```

Fetches a Jira ticket and transforms ADF content to clean markdown. Requires `jira_fetch.py` setup and `JIRA_TOKEN` env var.

## Configuration

### `.workflow/config.json`

| Setting | Default | Purpose |
|---------|---------|---------|
| `project_name` | `""` | Your project name |
| `tdd_policy` | `"pragmatic"` | TDD enforcement level |
| `tdd_exceptions` | `["UI layout/styling", "config files", "type definitions"]` | What skips TDD |
| `playwright_check` | `true` | Run Playwright after UI phases |
| `auto_commit` | `false` | Auto-commit after each task |
| `model_overrides` | `{...}` | Which model each agent uses |
| `jira.*` | — | Jira connection settings |

### Project-Specific Rules

Drop `.md` files in these directories:

- `.workflow/rules/planning/` — rules checked during plan review
- `.workflow/rules/code/` — rules checked during code review

Each rule file should have: Rule, Why, Correct example, Incorrect example, Exceptions.

## File Locations

### Always loaded (via `.claude/rules/`)
- `quality-criteria.md` — language-agnostic code quality
- `tdd-policy.md` — pragmatic TDD enforcement
- `security-gates.md` — blocked/gated commands
- `resume-protocol.md` — interrupted session recovery

### Generated during workflow
| File | Created by | Purpose |
|------|-----------|---------|
| `.workflow/project-overview.md` | `/init` | Project overview (loaded every session) |
| `.workflow/plans/{dir}/plan.md` | `/plan` | Execution plan |
| `.workflow/plans/{dir}/state.md` | `/execute` | Execution progress |
| `{Component}.analysis.md` | `/analyze` | Component deep-dive (co-located) |
| `.workflow/templates/{name}/template.md` | `/template-create` | Reusable pattern |

## Resuming Interrupted Work

If a session is interrupted, the next session automatically detects it:

> "Found interrupted execution: **user-export** — Phase 2, Task 3. Resume with `/execute --resume`."

State is saved in `state.md` with `[>]` markers showing exactly where work stopped, including sub-step progress.

## Cost Optimization

| Agent | Model | When |
|-------|-------|------|
| Planner | Opus | Creating plans (needs synthesis) |
| Analyzer (full) | Opus | First-time component analysis |
| Analyzer (update) | Sonnet | Incremental updates |
| Executor | Sonnet | Implementing tasks (mechanical) |
| Reviewer | Sonnet | Plan and code review (checklist-based) |
| Doc-updater | Sonnet | Change assessment (judgment, but not creative) |
| Template extractor | Opus | Pattern extraction (one-time, high-judgment) |
| Template applier | Sonnet | Variable substitution (mechanical) |

## Hooks

Three hooks run automatically:

1. **Security gate** (PreToolUse) — blocks catastrophic commands, asks confirmation for risky ones
2. **Quality check** (PostToolUse) — warns about debug output, empty catches, undescribed TODOs
3. **Context monitor** (PostToolUse) — warns at 35% remaining, critical at 25%, stop at 15%
