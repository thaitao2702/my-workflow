# AI Coding Workflow — Introduction

## What Is This?

A drop-in framework for Claude Code that gives AI agents **persistent memory, structured execution, and pattern reuse**. Copy two directories (`.claude/`, `.workflow/`) and a `CLAUDE.md` into any project, and the AI goes from ad-hoc prompting to a disciplined engineering process.

## The Problem

Without structure, every AI coding session starts from zero:
- The agent re-reads the same files, rediscovers the same architecture
- It makes the same wrong assumptions about component behavior
- Knowledge from previous sessions is completely lost
- Similar features are built from scratch every time
- Long tasks fail mid-way with no way to resume

## Two Core Pillars

### 1. Living Knowledge Layer

The system maintains persistent understanding of your codebase at two levels:

```
Project Level                         Component Level
┌───────────────────────┐             ┌───────────────────────────┐
│ project-overview.md   │             │ {Component}.analysis.md   │
│                       │             │                           │
│ Architecture, modules,│             │ Public API, hidden        │
│ core flows, data      │             │ behaviors, edge cases,    │
│ model, conventions    │             │ integration patterns,     │
│                       │             │ lessons learned from      │
│ Loaded every session  │             │ real implementations      │
└───────────────────────┘             └───────────────────────────┘
```

This isn't static documentation. It **grows with every execution**. When the executor discovers a hidden retry mechanism, an API that doesn't match expectations, or an edge case the plan missed — that finding is written back into the component's analysis doc. The next session that touches that component starts with all prior experience built in.

### 2. Pattern Reuse

Most projects have repeatable work — adding a new API endpoint, integrating a new provider, creating a new CRUD page. The first time is planned from scratch. After that, `/template-create` extracts the proven pattern:

- **What steps to follow** (and in what order)
- **What stays the same** `[F]` fixed — error handling, config registration
- **What values change** `[P]` parametric — names, paths, columns
- **What needs rethinking** `[G]` guided — business-specific logic, vendor differences

Next time: `/template-apply` fills in the variables and feeds enriched context to `/plan`, which adapts it to the current codebase state.

## The Workflow

```
/initialize ──► project-overview.md (run once)

/plan ──► reads knowledge layer ──► phased plan with tasks
  │       checks for matching templates
  │       user reviews and approves
  │
/execute ──► implements plan phase by phase
  │          TDD, code review, state tracking
  │          discovers hidden behaviors
  │
  ├──► /doc-update ──► captures discoveries into analysis docs
  │
  └──► /template-create ──► extracts pattern if repeatable
```

## Eight Commands

| Command | What It Does | When To Use |
|---------|-------------|-------------|
| `/initialize` | Scans project, produces overview with architecture diagrams | Once per project, or after major structural changes |
| `/plan` | Turns requirements into phased, dependency-aware execution plan | Starting any non-trivial feature or refactor |
| `/execute` | Implements plan with TDD, review per phase, resumable state | After `/plan` produces an approved plan |
| `/analyze` | Deep-analyzes a component, produces co-located `.analysis.md` | Before working on a complex component for the first time |
| `/doc-update` | Assesses code changes, patches analysis docs, captures discoveries | Automatically after `/execute`, or manually |
| `/template-create` | Extracts repeatable pattern from completed work | After `/execute` completes work that will be repeated |
| `/template-apply` | Applies template, collects variables, feeds to `/plan` | When building something similar to a previous implementation |
| `/jira` | Fetches Jira ticket as clean markdown | When requirements live in Jira |

## Architecture

**Orchestrator + Subagent model.** The main agent runs skills (workflow steps). Skills spawn specialized subagents for heavy work:

| Agent | Specialty | Model |
|-------|-----------|-------|
| Executor | TDD implementation, reports discoveries | Sonnet |
| Analyzer | Deep code analysis, bottom-up recursive | Opus |
| Reviewer | Quality checks for plans and code | Sonnet |
| Doc-Updater | Change assessment, surgical doc patches | Sonnet |
| Template-Extractor | Pattern abstraction via multi-case reasoning | Opus |
| Template-Applier | Variable substitution, plan input generation | Sonnet |

**Skills define WHAT to do** (workflow, data collection, verification). **Agents define HOW to think** (reasoning, judgment, domain expertise). They communicate through **prompt templates** — the skill collects context, fills the template, spawns the agent.

## Key Design Choices

- **Analysis docs are the primary source for planning** — hash-verified for freshness, contain accumulated experience that raw source code doesn't. Falls back to source only when stale or missing.
- **Templates always go through `/plan`** — templates accelerate planning, they don't bypass it. The codebase may have changed since the template was created.
- **Discoveries flow back into docs** — executor findings (hidden behaviors, wrong assumptions) are passed to `/doc-update` and written into analysis docs permanently.
- **JSON + CLI for state** — token-efficient, atomic writes, parallel-safe. Read one field (~20 tokens) instead of parsing a markdown file.
- **One executor per phase** — saves ~12k tokens compared to per-task spawning. The executor builds on its own work within a phase.
- **Pragmatic TDD** — tests first by default, documented exceptions for UI, config, types.

## Getting Started

```
1. Copy .claude/ and .workflow/ + CLAUDE.md into your project
2. Edit .workflow/config.json (set project_name)
3. /initialize
4. /plan "your feature"
5. /execute
```

For full details on each command, flow diagrams, configuration options, and directory structure, see the [README](../README.md).
