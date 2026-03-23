# GSD (Get Shit Done) — AI Workflow Framework

> **Source:** `E:/Project/My Workflow/gsd/`
> **npm package:** `get-shit-done-cc` v1.27.0
> **Author:** TÂCHES
> **License:** MIT

---

## Table of Contents

1. [Overview / Purpose](#overview--purpose)
2. [Key Features](#key-features)
3. [Folder Structure](#folder-structure)
4. [Core Components](#core-components)
5. [How It Works](#how-it-works)
6. [Agents](#agents)
7. [Commands Reference](#commands-reference)
8. [Configuration](#configuration)
9. [Usage Guide](#usage-guide)
10. [Notable Patterns and Design Decisions](#notable-patterns-and-design-decisions)
11. [Security](#security)
12. [Troubleshooting](#troubleshooting)

---

## Overview / Purpose

GSD is a **meta-prompting, context engineering, and spec-driven development framework** for AI coding assistants. It sits as an orchestration layer between the user and AI coding runtimes (Claude Code, OpenCode, Gemini CLI, Codex, Copilot, Cursor, Antigravity).

Its core problem statement: **context rot** — the quality degradation that happens as an AI coding session accumulates conversation history and fills its context window. As Claude's context window fills with accumulated work, quality degrades, reasoning shortcuts appear, and "I'll be more concise now" behavior emerges.

GSD solves this by:

- Keeping the main orchestrator context lean (10–15% usage)
- Spawning specialized subagents with fresh 200K-token context windows for each task
- Storing all project state as human-readable files in `.planning/` so context is never lost across sessions
- Breaking work into atomic, verifiable units with structured XML plans

The framework is designed for **solo developers** and small teams who want to describe what they want built and have it reliably produced — without the overhead of enterprise project management tooling.

---

## Key Features

### Context Engineering
GSD generates a set of structured artifacts (PROJECT.md, REQUIREMENTS.md, ROADMAP.md, STATE.md, PLAN.md files) that give the AI exactly the right context at each stage. File size limits are calibrated to where Claude's quality degrades.

### Multi-Agent Orchestration
Each workflow stage uses a thin orchestrator that spawns specialized agents:
- 4 parallel researchers during project initialization and phase planning
- Multiple parallel executor agents during phase execution (wave-based)
- Sequential verifiers and checkers after each execution wave

### Spec-Driven Development Pipeline
The full cycle: questions → research → requirements → roadmap → discuss → plan → execute → verify → ship. Each stage feeds the next with structured, inspectable artifacts.

### Wave-Based Parallel Execution
Plans are grouped into dependency waves. Plans in the same wave run in parallel; waves run sequentially. Each executor gets a fresh 200K context window, producing atomic git commits per task.

### File-Based State Management
All state lives in `.planning/` as human-readable Markdown and JSON. No database, no server. State survives context resets (`/clear`), can be inspected by humans, and can be committed to git for team visibility.

### Multi-Runtime Support
A single codebase supports Claude Code, OpenCode, Gemini CLI, Codex, GitHub Copilot, Cursor, and Antigravity. The installer transforms content per runtime at install time.

### UI Design Contract System
`/gsd:ui-phase` locks a design contract (spacing, typography, color, copywriting standards) before frontend work begins. `/gsd:ui-review` performs a retroactive 6-pillar visual audit after execution.

### Nyquist Validation Layer
During plan-phase research, GSD maps automated test coverage to each phase requirement before any code is written. The plan-checker enforces this as an 8th verification dimension — plans where tasks lack automated verify commands are not approved.

### TDD Integration
Plans can be typed `tdd`, triggering a red-green-refactor execution cycle with atomic commits per phase.

### Session Management
`/gsd:pause-work` creates a structured handoff file (HANDOFF.json + continue-here.md). `/gsd:resume-work` restores full context. The context monitor hook warns agents when the context window is running low.

---

## Folder Structure

```
gsd/
├── agents/                     # 16 specialized agent definitions (.md)
├── assets/                     # Logo images and terminal SVG
├── bin/
│   └── install.js              # npm package installer (~3,000 lines)
├── commands/
│   └── gsd/                    # 44 user-facing slash command files (.md)
├── docs/                       # Documentation
│   ├── AGENTS.md               # Agent reference
│   ├── ARCHITECTURE.md         # System architecture
│   ├── CLI-TOOLS.md            # gsd-tools.cjs API reference
│   ├── COMMANDS.md             # Full command syntax reference
│   ├── CONFIGURATION.md        # Full config.json schema
│   ├── FEATURES.md             # Feature reference
│   ├── README.md               # Docs index
│   ├── USER-GUIDE.md           # Detailed user guide
│   ├── context-monitor.md      # Context window monitor docs
│   ├── superpowers/            # Internal development plans
│   └── zh-CN/                  # Simplified Chinese documentation
├── get-shit-done/              # Core framework files
│   ├── bin/
│   │   ├── gsd-tools.cjs       # Main CLI utility (entry point)
│   │   └── lib/                # 17 domain modules
│   │       ├── commands.cjs    # Slug, timestamp, todos, scaffold, stats
│   │       ├── config.cjs      # config.json read/write
│   │       ├── core.cjs        # Error handling, output formatting
│   │       ├── frontmatter.cjs # YAML frontmatter CRUD
│   │       ├── init.cjs        # Compound context loading
│   │       ├── milestone.cjs   # Milestone archival
│   │       ├── model-profiles.cjs  # Model profile resolution
│   │       ├── phase.cjs       # Phase directory operations
│   │       ├── profile-output.cjs  # Developer profile formatting
│   │       ├── profile-pipeline.cjs # Session analysis pipeline
│   │       ├── roadmap.cjs     # ROADMAP.md parsing
│   │       ├── security.cjs    # Path traversal, injection detection
│   │       ├── state.cjs       # STATE.md parsing and updates
│   │       ├── template.cjs    # Template selection and filling
│   │       ├── uat.cjs         # UAT audit support
│   │       └── verify.cjs      # Plan/phase validation
│   ├── references/             # Shared knowledge docs (13 files)
│   │   ├── checkpoints.md      # Checkpoint types and patterns
│   │   ├── continuation-format.md  # Agent continuation protocol
│   │   ├── decimal-phase-calculation.md
│   │   ├── git-integration.md  # Git commit patterns
│   │   ├── git-planning-commit.md
│   │   ├── model-profile-resolution.md
│   │   ├── model-profiles.md   # Per-agent model assignments
│   │   ├── phase-argument-parsing.md
│   │   ├── planning-config.md  # Config schema documentation
│   │   ├── questioning.md      # Project initialization philosophy
│   │   ├── tdd.md              # TDD integration patterns
│   │   ├── ui-brand.md         # Visual output formatting
│   │   ├── user-profiling.md
│   │   └── verification-patterns.md  # Stub detection and wiring checks
│   ├── templates/              # Planning artifact templates
│   │   ├── codebase/           # Brownfield mapping templates (7 files)
│   │   ├── research-project/   # Research output templates (5 files)
│   │   ├── claude-md.md        # CLAUDE.md template
│   │   ├── config.json         # Default config template
│   │   ├── context.md          # CONTEXT.md template
│   │   ├── continue-here.md    # Session handoff template
│   │   ├── copilot-instructions.md
│   │   ├── DEBUG.md            # Debug session template
│   │   ├── dev-preferences.md
│   │   ├── discovery.md        # Discovery phase template
│   │   ├── discussion-log.md   # Discussion audit trail
│   │   ├── milestone.md        # Milestone entry template
│   │   ├── milestone-archive.md
│   │   ├── phase-prompt.md     # Phase execution prompt template
│   │   ├── planner-subagent-prompt.md
│   │   ├── project.md          # PROJECT.md template
│   │   ├── requirements.md     # REQUIREMENTS.md template
│   │   ├── research.md         # RESEARCH.md template
│   │   ├── retrospective.md
│   │   ├── roadmap.md          # ROADMAP.md template
│   │   ├── state.md            # STATE.md template
│   │   ├── summary.md          # SUMMARY.md template
│   │   ├── summary-complex.md  # Granularity-aware summary variants
│   │   ├── summary-minimal.md
│   │   ├── summary-standard.md
│   │   ├── UAT.md              # User acceptance testing template
│   │   ├── UI-SPEC.md          # UI design contract template
│   │   ├── user-profile.md     # Developer behavioral profile template
│   │   ├── user-setup.md
│   │   ├── VALIDATION.md       # Nyquist validation template
│   │   └── verification-report.md
│   └── workflows/              # 46 orchestration workflow files (.md)
├── hooks/                      # Runtime hook source files
│   ├── gsd-check-update.js     # Version update checker
│   ├── gsd-context-monitor.js  # Context window usage warnings
│   ├── gsd-prompt-guard.js     # Prompt injection scanner
│   ├── gsd-statusline.js       # Status bar display
│   └── gsd-workflow-guard.js   # File edit context guard
├── scripts/
│   ├── build-hooks.js          # Hook compilation script
│   └── run-tests.cjs           # Test runner
├── tests/                      # Test suite (40+ test files)
├── .github/                    # GitHub workflows, issue templates
├── CHANGELOG.md                # Version history
├── LICENSE                     # MIT
├── package.json                # npm package definition
├── README.md                   # Main README
├── README.zh-CN.md             # Chinese README
└── SECURITY.md                 # Security policy
```

### Project Files Created in `.planning/`

When GSD initializes a project, it creates this structure in the target repository:

```
.planning/
├── PROJECT.md              # Living project context — vision, requirements, decisions
├── REQUIREMENTS.md         # Scoped v1/v2/out-of-scope requirements with REQ-IDs
├── ROADMAP.md              # Phase breakdown with status tracking
├── STATE.md                # Living memory — position, decisions, blockers, metrics
├── config.json             # Workflow configuration
├── MILESTONES.md           # Completed milestone archive
├── HANDOFF.json            # Structured session handoff (from /gsd:pause-work)
├── research/               # Domain research from /gsd:new-project
│   ├── SUMMARY.md
│   ├── STACK.md
│   ├── FEATURES.md
│   ├── ARCHITECTURE.md
│   └── PITFALLS.md
├── codebase/               # Brownfield codebase mapping (from /gsd:map-codebase)
│   ├── STACK.md
│   ├── ARCHITECTURE.md
│   ├── CONVENTIONS.md
│   ├── CONCERNS.md
│   ├── STRUCTURE.md
│   ├── TESTING.md
│   └── INTEGRATIONS.md
├── phases/
│   └── XX-phase-name/
│       ├── XX-CONTEXT.md       # User preferences (from /gsd:discuss-phase)
│       ├── XX-RESEARCH.md      # Ecosystem research (from /gsd:plan-phase)
│       ├── XX-YY-PLAN.md       # Execution plans (XML structure)
│       ├── XX-YY-SUMMARY.md    # Execution outcomes
│       ├── XX-VERIFICATION.md  # Post-execution verification
│       ├── XX-VALIDATION.md    # Nyquist test coverage mapping
│       ├── XX-UI-SPEC.md       # UI design contract (from /gsd:ui-phase)
│       ├── XX-UI-REVIEW.md     # Visual audit scores (from /gsd:ui-review)
│       └── XX-UAT.md           # User acceptance test results
├── quick/                  # Quick task tracking
│   └── YYMMDD-xxx-slug/
│       ├── PLAN.md
│       └── SUMMARY.md
├── todos/
│   ├── pending/            # Captured ideas
│   └── done/               # Completed todos
├── threads/                # Persistent cross-session context threads
├── seeds/                  # Forward-looking ideas with trigger conditions
├── debug/                  # Active debug sessions
│   ├── *.md
│   ├── resolved/
│   └── knowledge-base.md   # Persistent debug learnings
├── reports/                # Session reports
└── ui-reviews/             # Screenshots from /gsd:ui-review (gitignored)
```

---

## Core Components

### Command Files (`commands/gsd/*.md`)

Each file is a user-facing slash command. They contain YAML frontmatter specifying the command name, description, and allowed tools, plus a prompt body that bootstraps the workflow.

Commands are installed differently per runtime:
- **Claude Code / Gemini / Copilot:** Custom slash commands (`/gsd:command-name`)
- **OpenCode:** Slash commands (`/gsd-command-name`)
- **Codex:** Skills (`$gsd-command-name`)

The command file typically does minimal work itself — it loads context via `gsd-tools.cjs init` and then references the corresponding workflow file.

### Workflow Files (`get-shit-done/workflows/*.md`)

The orchestration logic. Each workflow contains the detailed step-by-step process:
- Context loading via `gsd-tools.cjs init <workflow> <phase>`
- Agent spawn instructions with model resolution
- Gate and checkpoint definitions
- State update patterns
- Error handling and recovery logic

Workflows are the "brain" — they coordinate agents but never do heavy implementation work themselves. The key design constraint: orchestrators stay at 10–15% context usage, leaving room for coordination across the entire phase.

Key workflows include:
- `new-project.md` — Full project initialization pipeline
- `plan-phase.md` — Research + plan + verify cycle
- `execute-phase.md` — Wave-based parallel execution
- `verify-work.md` — User acceptance testing with auto-diagnosis
- `quick.md` — Ad-hoc task execution
- `transition.md` — Internal phase transition (called by auto-advance)

### Agent Files (`agents/*.md`)

Specialized agent definitions. Each has YAML frontmatter specifying:
- `name` — Agent identifier (e.g., `gsd-executor`)
- `description` — Role and purpose
- `tools` — Allowed tool access (principle of least privilege)
- `color` — Terminal output color for visual distinction

Agents are spawned by orchestrators via `Task(subagent_type="gsd-executor", model="...", prompt="...")`. Each gets a fresh context window.

### CLI Tools (`get-shit-done/bin/gsd-tools.cjs`)

A Node.js CLI utility that is the backbone of all GSD automation. Workflows call it via bash to:
- Load compound context for a workflow type
- Read and update STATE.md (with file locking for parallel safety)
- Parse and update ROADMAP.md
- Resolve model for each agent based on current profile
- Commit files with proper formatting
- Fill templates, manage phases, run verifications

The CLI has 17 domain modules. The most important:

| Module | What It Does |
|--------|--------------|
| `init.cjs` | Loads all context for a workflow in one call, returns JSON |
| `state.cjs` | Full STATE.md lifecycle — parse, update, lock on concurrent write |
| `phase.cjs` | Phase directory CRUD, decimal numbering, plan indexing |
| `roadmap.cjs` | ROADMAP.md parsing, phase extraction, progress updates |
| `model-profiles.cjs` | Maps agent names to model tiers based on active profile |
| `security.cjs` | Path traversal prevention, prompt injection detection |
| `verify.cjs` | Plan structure validation, phase completeness checks |
| `template.cjs` | Template selection (granularity-aware) and variable filling |

### Hooks (`hooks/`)

Runtime hooks that integrate with the host AI agent's event system:

| Hook | Event | What It Does |
|------|-------|--------------|
| `gsd-statusline.js` | `statusLine` | Displays model, task, directory, context usage bar. Writes context metrics to `/tmp/claude-ctx-{session}.json` |
| `gsd-context-monitor.js` | `PostToolUse` / `AfterTool` | Reads context metrics from bridge file; injects WARNING at ≤35% remaining, CRITICAL at ≤25% |
| `gsd-check-update.js` | `SessionStart` | Background check for new GSD versions |
| `gsd-prompt-guard.js` | `PreToolUse` | Scans writes to `.planning/` for prompt injection patterns (advisory, never blocking) |
| `gsd-workflow-guard.js` | `PreToolUse` | Warns on file edits outside GSD workflow context (opt-in) |

Hooks are compiled by `scripts/build-hooks.js` (using esbuild) and distributed as `hooks/dist/` files.

### Reference Files (`get-shit-done/references/*.md`)

Shared knowledge documents that workflows and agents reference with `@`-syntax. Key references:

| File | Contains |
|------|----------|
| `checkpoints.md` | The three checkpoint types (human-verify, decision, human-action), examples, anti-patterns, automation reference tables |
| `verification-patterns.md` | How to detect stubs vs real implementations; wiring verification for React components, API routes, database schemas |
| `model-profiles.md` | Per-agent model tier table, profile philosophy, rationale for each choice |
| `git-integration.md` | Commit format conventions, per-task atomicity rationale, multi-repo workspace support |
| `questioning.md` | "Dream extraction" philosophy for project initialization — how to ask questions collaboratively |
| `tdd.md` | Red-green-refactor cycle, when to use TDD vs standard plans, commit patterns |
| `planning-config.md` | Full config.json schema documentation |

### Templates (`get-shit-done/templates/`)

Markdown templates for all planning artifacts. Used by `gsd-tools.cjs template fill` and `scaffold` commands. Notable templates:

- `project.md` — PROJECT.md structure with Requirements (Validated/Active/Out of Scope), Core Value, Key Decisions
- `state.md` — STATE.md with YAML frontmatter for machine parsing + human-readable body sections
- `phase-prompt.md` — Used when spawning executor agents
- `summary.md` / `summary-minimal.md` / `summary-standard.md` / `summary-complex.md` — Granularity-aware summary templates selected based on the `granularity` config setting
- `UAT.md` — User acceptance testing results tracking
- `VALIDATION.md` — Nyquist test coverage contract
- `UI-SPEC.md` — Design contract for frontend phases

### Installer (`bin/install.js`)

A ~3,000-line installer that handles:
1. Runtime detection (interactive prompt or CLI flags)
2. Location selection (global vs local)
3. File deployment (copies commands, workflows, references, templates, agents, hooks)
4. Per-runtime transformation (tool name mapping, frontmatter format, event names, path conventions)
5. Hook registration in the runtime's `settings.json`
6. Backup of locally modified files to `gsd-local-patches/` before overwriting
7. Manifest tracking in `gsd-file-manifest.json` for clean uninstall
8. `--uninstall` mode

---

## How It Works

### Full Project Lifecycle

```
/gsd:new-project
    Questions (dream extraction philosophy)
        |
        v
    4x Project Researchers (parallel)
        Stack | Features | Architecture | Pitfalls
        |
        v
    Research Synthesizer → SUMMARY.md
        |
        v
    Requirements extraction → REQUIREMENTS.md
        |
        v
    Roadmapper → ROADMAP.md
        |
        v
    User approval → STATE.md initialized

    FOR EACH PHASE:
        /gsd:discuss-phase N      ← Lock in user preferences → CONTEXT.md
        /gsd:ui-phase N           ← Design contract (frontend phases) → UI-SPEC.md
        /gsd:plan-phase N         ← Research + Plan + Verify → RESEARCH.md + PLAN.md files
        /gsd:execute-phase N      ← Wave-based parallel execution → code + SUMMARY.md + VERIFICATION.md
        /gsd:verify-work N        ← Manual UAT → UAT.md
        /gsd:ship N               ← Create PR
        /gsd:ui-review N          ← Visual audit (frontend phases)

    /gsd:audit-milestone
    /gsd:complete-milestone       ← Archive + git tag
    /gsd:new-milestone            ← Start next version cycle
```

### Wave Execution Model

During `execute-phase`, plans are analyzed for dependencies and grouped into waves:

```
Wave 1 (parallel):   Plan 01, Plan 02   (no dependencies)
Wave 2 (parallel):   Plan 03, Plan 04   (depend on Wave 1)
Wave 3 (sequential): Plan 05            (depends on both Wave 2 plans)
```

Each plan in a wave spawns a fresh `gsd-executor` agent with a clean 200K context window. Agents commit with `--no-verify` during parallel waves to avoid pre-commit hook lock contention; the orchestrator runs hooks once after each wave completes.

STATE.md writes use file-level locking (`STATE.md.lock` with atomic `O_EXCL` creation) to prevent concurrent write corruption across parallel agents.

### Context Propagation

Each workflow stage produces artifacts that feed subsequent stages:

```
PROJECT.md          → All agents (always loaded)
REQUIREMENTS.md     → Planner, Verifier, Auditor
ROADMAP.md          → Orchestrators
STATE.md            → All agents (decisions, blockers, position)
CONTEXT.md          → Phase Researcher, Planner, Executor
RESEARCH.md         → Planner, Plan Checker
PLAN.md             → Executor, Plan Checker
SUMMARY.md          → Verifier, state tracking
UI-SPEC.md          → Executor, UI Auditor
```

### Plan Structure

Plans use XML structure optimized for Claude:

```xml
---
phase: 03-user-auth
plan: 02
type: auto
wave: 1
depends_on: []
---

<objective>
Create login endpoint with JWT authentication.
</objective>

<context>
@.planning/PROJECT.md
@.planning/STATE.md
@src/types/user.ts
</context>

<task type="auto">
  <name>Create login endpoint</name>
  <files>src/app/api/auth/login/route.ts</files>
  <action>
    Use jose for JWT (not jsonwebtoken - CommonJS issues).
    Validate credentials against users table.
    Return httpOnly cookie on success.
  </action>
  <verify>curl -X POST localhost:3000/api/auth/login returns 200 + Set-Cookie</verify>
  <done>Valid credentials return cookie, invalid return 401</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Login endpoint with JWT authentication</what-built>
  <how-to-verify>
    1. POST /api/auth/login with valid credentials → 200 + Set-Cookie header
    2. POST /api/auth/login with invalid credentials → 401
    3. Cookie is httpOnly and Secure
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues</resume-signal>
</task>
```

### Git Commit Strategy

GSD commits one atomic commit per completed task (not per plan):

```
feat(04-01): add webhook signature verification
feat(04-01): implement payment session creation
feat(04-01): create checkout page component
docs(04-01): complete checkout flow plan
```

This makes every change independently revertable, enables `git bisect` to find exact failing tasks, and provides rich context for future AI sessions reading the git log.

### Plan Verification Loop

Before any plan is executed, the `gsd-plan-checker` agent validates it across 8 dimensions:

1. Requirement coverage — Does the plan address the phase's requirements?
2. Task atomicity — Are tasks small enough for a single context window?
3. Dependency ordering — Are dependencies correctly sequenced?
4. File scope — Are file modifications scoped correctly?
5. Verification commands — Does every task have a runnable verify step?
6. Context fit — Will this fit in a 200K context window?
7. Gap detection — Are there missing pieces?
8. Nyquist compliance — Does every requirement have an automated test command?

If the checker returns FAIL, the planner revises and the loop repeats (max 3 iterations).

---

## Agents

GSD has 16 specialized agents, each with a focused role and principle-of-least-privilege tool access.

### Researcher Agents

| Agent | Role | Parallelism | Key Tools |
|-------|------|-------------|-----------|
| `gsd-project-researcher` | Researches domain ecosystem for new projects | 4 parallel (stack, features, architecture, pitfalls) | Read, Write, Bash, WebSearch, WebFetch, MCP |
| `gsd-phase-researcher` | Researches implementation approaches for a phase | 4 parallel | Read, Write, Bash, WebSearch, WebFetch, MCP |
| `gsd-ui-researcher` | Produces UI design contracts | Single | Read, Write, Bash, WebSearch, WebFetch, MCP |
| `gsd-research-synthesizer` | Combines parallel researcher outputs | Single (after researchers) | Read, Write, Bash |

### Planning Agents

| Agent | Role | Model (balanced) |
|-------|------|-----------------|
| `gsd-planner` | Creates atomic task plans with XML structure | Opus |
| `gsd-roadmapper` | Creates phase roadmaps with requirement mapping | Sonnet |

### Execution Agents

| Agent | Role | Context |
|-------|------|---------|
| `gsd-executor` | Executes plans, makes atomic commits | Fresh 200K window per plan |

### Checker/Verifier Agents

| Agent | Role | Access |
|-------|------|--------|
| `gsd-plan-checker` | Pre-execution plan verification (8 dimensions) | Read-only |
| `gsd-integration-checker` | Cross-phase integration verification | Read-only |
| `gsd-ui-checker` | UI-SPEC.md quality validation | Read-only |
| `gsd-verifier` | Post-execution goal achievement verification | Read + Write (VERIFICATION.md) |
| `gsd-nyquist-auditor` | Fills test coverage gaps (never modifies implementation) | Read, Write, Edit, Bash |
| `gsd-ui-auditor` | 6-pillar visual audit of implemented frontend | Read, Write, Bash |

### Utility Agents

| Agent | Role |
|-------|------|
| `gsd-codebase-mapper` | Maps existing codebase structure (4 parallel, Haiku model) |
| `gsd-debugger` | Scientific-method debugging with persistent state across sessions |
| `gsd-user-profiler` | Analyzes session messages across 8 behavioral dimensions |

### Agent Tool Permissions (Principle of Least Privilege)

- **Checkers** are read-only — they evaluate but never modify
- **Researchers** have web access — they need current ecosystem information
- **Executors** have Edit but no web access — they implement from plan instructions
- **Mappers** have Write but not Edit — they write analysis documents, not code

---

## Commands Reference

### Core Workflow Commands (44 total)

| Command | Purpose |
|---------|---------|
| `/gsd:new-project [--auto @file.md]` | Full initialization: questions → research → requirements → roadmap |
| `/gsd:discuss-phase [N] [--auto] [--batch] [--analyze]` | Capture implementation decisions before planning |
| `/gsd:ui-phase [N]` | Generate UI design contract for frontend phases |
| `/gsd:plan-phase [N] [--auto] [--skip-research] [--skip-verify]` | Research + plan + verify |
| `/gsd:execute-phase <N> [--wave N]` | Execute all plans in parallel waves |
| `/gsd:verify-work [N]` | Manual user acceptance testing with auto-diagnosis |
| `/gsd:ship [N] [--draft]` | Create PR from verified phase work |
| `/gsd:next` | Auto-detect and run next logical step |
| `/gsd:fast <text>` | Inline trivial tasks — no subagents, no planning overhead |
| `/gsd:autonomous [--from N]` | Run all remaining phases autonomously |
| `/gsd:audit-milestone` | Verify milestone met its definition of done |
| `/gsd:complete-milestone` | Archive milestone, create git tag |
| `/gsd:new-milestone [name] [--reset-phase-numbers]` | Start next version cycle |

### Phase Management

| Command | Purpose |
|---------|---------|
| `/gsd:add-phase` | Append new phase to roadmap |
| `/gsd:insert-phase [N]` | Insert urgent work using decimal numbering (e.g., 3.1) |
| `/gsd:remove-phase [N]` | Remove future phase and renumber |
| `/gsd:list-phase-assumptions [N]` | Preview Claude's intended approach before planning |
| `/gsd:plan-milestone-gaps` | Create phases to close gaps found in audit |
| `/gsd:research-phase [N]` | Deep ecosystem research standalone |
| `/gsd:validate-phase [N]` | Retroactively audit and fill Nyquist validation gaps |

### UI Design

| Command | Purpose |
|---------|---------|
| `/gsd:ui-phase [N]` | Generate UI-SPEC.md design contract |
| `/gsd:ui-review [N]` | Retroactive 6-pillar visual audit |

### Session & Navigation

| Command | Purpose |
|---------|---------|
| `/gsd:progress` | Show status and next steps |
| `/gsd:pause-work` | Save structured handoff (HANDOFF.json + continue-here.md) |
| `/gsd:resume-work` | Restore full context from last session |
| `/gsd:session-report` | Generate session summary with work and outcomes |
| `/gsd:help` | Show all commands |
| `/gsd:update` | Update GSD with changelog preview |

### Code Quality

| Command | Purpose |
|---------|---------|
| `/gsd:review --phase N [--gemini] [--claude] [--all]` | Cross-AI peer review |
| `/gsd:pr-branch` | Create clean PR branch filtering `.planning/` commits |
| `/gsd:audit-uat` | Cross-phase audit of outstanding UAT items |

### Backlog, Seeds, and Threads

| Command | Purpose |
|---------|---------|
| `/gsd:add-backlog <desc>` | Add idea to backlog parking lot (999.x numbering) |
| `/gsd:review-backlog` | Promote/keep/remove backlog items |
| `/gsd:plant-seed <idea>` | Forward-looking idea with trigger conditions — surfaces at right milestone |
| `/gsd:thread [name]` | Persistent cross-session context threads |

### Utilities

| Command | Purpose |
|---------|---------|
| `/gsd:quick [--full] [--discuss] [--research]` | Ad-hoc task with GSD guarantees |
| `/gsd:debug [desc]` | Systematic debugging with persistent state |
| `/gsd:do <text>` | Route freeform text to right GSD command |
| `/gsd:note <text>` | Zero-friction idea capture |
| `/gsd:add-todo [desc]` | Capture idea for later |
| `/gsd:check-todos` | List pending todos |
| `/gsd:add-tests [N]` | Generate tests for a completed phase |
| `/gsd:stats` | Display project statistics |
| `/gsd:health [--repair]` | Validate `.planning/` directory integrity |
| `/gsd:cleanup` | Archive accumulated phase directories |
| `/gsd:settings` | Interactive configuration |
| `/gsd:set-profile <profile>` | Quick model profile switch |
| `/gsd:profile-user [--questionnaire] [--refresh]` | Generate developer behavioral profile |
| `/gsd:map-codebase [area]` | Analyze existing codebase (brownfield) |
| `/gsd:reapply-patches` | Restore local modifications after GSD update |

---

## Configuration

GSD stores project settings in `.planning/config.json`. Created during `/gsd:new-project`, updated via `/gsd:settings`.

### Full Schema

```json
{
  "mode": "interactive",
  "granularity": "standard",
  "model_profile": "balanced",
  "model_overrides": {},
  "planning": {
    "commit_docs": true,
    "search_gitignored": false,
    "sub_repos": []
  },
  "workflow": {
    "research": true,
    "plan_check": true,
    "verifier": true,
    "auto_advance": false,
    "nyquist_validation": true,
    "ui_phase": true,
    "ui_safety_gate": true,
    "node_repair": true,
    "node_repair_budget": 2,
    "research_before_questions": false
  },
  "hooks": {
    "context_warnings": true,
    "workflow_guard": false
  },
  "parallelization": {
    "enabled": true,
    "plan_level": true,
    "task_level": false,
    "skip_checkpoints": true,
    "max_concurrent_agents": 3,
    "min_plans_for_parallel": 2
  },
  "git": {
    "branching_strategy": "none",
    "phase_branch_template": "gsd/phase-{phase}-{slug}",
    "milestone_branch_template": "gsd/{milestone}-{slug}",
    "quick_branch_template": null
  },
  "gates": {
    "confirm_project": true,
    "confirm_phases": true,
    "confirm_roadmap": true,
    "confirm_breakdown": true,
    "confirm_plan": true,
    "execute_next_plan": true,
    "issues_review": true,
    "confirm_transition": true
  },
  "safety": {
    "always_confirm_destructive": true,
    "always_confirm_external_services": true
  }
}
```

### Core Settings

| Setting | Options | Default | What It Controls |
|---------|---------|---------|------------------|
| `mode` | `interactive`, `yolo` | `interactive` | `yolo` auto-approves all decisions |
| `granularity` | `coarse`, `standard`, `fine` | `standard` | Phase count: 3–5, 5–8, or 8–12 phases |
| `model_profile` | `quality`, `balanced`, `budget`, `inherit` | `balanced` | Model tier per agent |

### Model Profiles

| Agent | `quality` | `balanced` | `budget` | `inherit` |
|-------|-----------|------------|----------|-----------|
| gsd-planner | Opus | Opus | Sonnet | Inherit |
| gsd-executor | Opus | Sonnet | Sonnet | Inherit |
| gsd-phase-researcher | Opus | Sonnet | Haiku | Inherit |
| gsd-project-researcher | Opus | Sonnet | Haiku | Inherit |
| gsd-research-synthesizer | Sonnet | Sonnet | Haiku | Inherit |
| gsd-roadmapper | Opus | Sonnet | Sonnet | Inherit |
| gsd-debugger | Opus | Sonnet | Sonnet | Inherit |
| gsd-verifier | Sonnet | Sonnet | Haiku | Inherit |
| gsd-plan-checker | Sonnet | Sonnet | Haiku | Inherit |
| gsd-codebase-mapper | Sonnet | Haiku | Haiku | Inherit |
| gsd-nyquist-auditor | Sonnet | Sonnet | Haiku | Inherit |

**Use `inherit` for non-Anthropic providers** (OpenRouter, local models) to prevent GSD from calling Anthropic models for subagents.

### Scenario Presets

| Scenario | mode | granularity | profile | research | plan_check | verifier |
|----------|------|-------------|---------|----------|------------|----------|
| Prototyping | `yolo` | `coarse` | `budget` | off | off | off |
| Normal development | `interactive` | `standard` | `balanced` | on | on | on |
| Production release | `interactive` | `fine` | `quality` | on | on | on |

### Git Branching

| Strategy | Creates Branch | Best For |
|----------|----------------|----------|
| `none` | Never | Solo development (default) |
| `phase` | Per `execute-phase` | Code review per phase |
| `milestone` | At first `execute-phase` | Release branches |

### Global Defaults

Save settings as global defaults at `~/.gsd/defaults.json`. New projects merge global defaults into their initial `config.json`.

---

## Usage Guide

### Installation

```bash
npx get-shit-done-cc@latest
```

The installer prompts for:
1. **Runtime** — Claude Code, OpenCode, Gemini, Codex, Copilot, Cursor, Antigravity, or all
2. **Location** — Global (all projects, `~/.claude/`) or local (current project, `./.claude/`)

Non-interactive flags:
```bash
npx get-shit-done-cc --claude --global   # Claude Code, global
npx get-shit-done-cc --claude --local    # Claude Code, local
npx get-shit-done-cc --all --global      # All runtimes, global
```

Verify installation: `/gsd:help`

### Recommended: Skip Permissions Mode

GSD is designed for frictionless automation. Run Claude Code with:

```bash
claude --dangerously-skip-permissions
```

Alternatively, add granular permissions to `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(date:*)", "Bash(echo:*)", "Bash(cat:*)", "Bash(ls:*)",
      "Bash(mkdir:*)", "Bash(git add:*)", "Bash(git commit:*)",
      "Bash(git status:*)", "Bash(git log:*)", "Bash(git diff:*)"
    ]
  }
}
```

### New Project (Full Cycle)

```bash
# Start Claude Code
claude --dangerously-skip-permissions

# 1. Initialize project (answers questions, research, requirements, roadmap)
/gsd:new-project
/clear

# 2. For each phase (clear context between major steps)
/gsd:discuss-phase 1        # Lock in your preferences → CONTEXT.md
/gsd:ui-phase 1             # Design contract (frontend phases) → UI-SPEC.md
/gsd:plan-phase 1           # Research + plan + verify → PLAN.md files
/gsd:execute-phase 1        # Parallel execution → code + commits
/gsd:verify-work 1          # Manual UAT → UAT.md
/gsd:ship 1                 # Create PR
/gsd:ui-review 1            # Visual audit (optional, frontend phases)
/clear

# Or use auto-detect for next step
/gsd:next

# 3. Complete milestone
/gsd:audit-milestone
/gsd:complete-milestone
/gsd:session-report
```

### Existing Codebase (Brownfield)

```bash
/gsd:map-codebase       # Parallel agents analyze: stack, arch, conventions, concerns
/gsd:new-project        # Questions focus on what you're ADDING, not rebuilding
# Normal phase workflow from here
```

### Quick Tasks (No Full Planning)

```bash
/gsd:quick
> "Fix the login button not responding on mobile Safari"

# With optional stages
/gsd:quick --discuss --research --full
```

### Quick Fix (Trivial, Inline)

```bash
/gsd:fast "fix typo in README"
/gsd:fast "add .env to gitignore"
```

### Resuming After a Break

```bash
/gsd:progress           # See where you left off
# or
/gsd:resume-work        # Full context restoration
```

### Scope Changes Mid-Milestone

```bash
/gsd:add-phase          # Append new phase
/gsd:insert-phase 3     # Insert between phases 3 and 4 → creates 3.1
/gsd:remove-phase 7     # Descope phase 7, renumber 8→7
```

### Preparing for Release

```bash
/gsd:audit-milestone        # Check requirements coverage, detect stubs
/gsd:audit-uat              # Find phases missing UAT
/gsd:plan-milestone-gaps    # Create phases to close gaps
/gsd:complete-milestone     # Archive, tag, done
```

### Updating GSD

```bash
npx get-shit-done-cc@latest
# If you had local modifications, restore them:
/gsd:reapply-patches
```

### Uninstalling

```bash
npx get-shit-done-cc --claude --global --uninstall
npx get-shit-done-cc --claude --local --uninstall
```

---

## Notable Patterns and Design Decisions

### Absent = Enabled

Workflow feature flags follow the **absent = enabled** pattern. If a key is missing from `config.json`, it defaults to `true`. Users explicitly disable features; they don't need to enable defaults. This means new config keys introduced in updates are automatically active for existing projects.

### Thin Orchestrators

Workflow files never do heavy lifting. They load context, spawn specialized agents, collect results, and route to the next step. The orchestrator itself stays at 10–15% context usage. All heavy work happens in fresh agent context windows.

### File-Based State as the Single Source of Truth

All project state lives in `.planning/` as human-readable files. This means:
- State survives context resets (`/clear`)
- Both humans and agents can inspect and modify state
- State can be committed to git for team visibility
- No external services or databases required

### Defense-in-Depth Verification

Multiple layers catch failures before they compound:
1. **Plan-checker** verifies plans before execution (8 dimensions, max 3 iterations)
2. **Nyquist validation** ensures every requirement has an automated test command
3. **Atomic commits** make every task independently revertable
4. **Wave verification** runs regression tests before proceeding to next wave
5. **Post-execution verifier** checks goal achievement, not just task completion
6. **UAT** provides human verification as the final gate

### Checkpoint Philosophy

Plans can contain three checkpoint types:
- **`human-verify`** (90%) — Claude automated everything, user visually confirms
- **`decision`** (9%) — User makes architectural/technology choices
- **`human-action`** (1%) — Truly unavoidable manual steps (email verification, 3DS payments)

Golden rule: **If Claude can automate it, Claude must automate it.** Checkpoints are never used to ask users to run CLI commands or perform work that has an API equivalent.

### Dream Extraction Philosophy

Project initialization uses a "dream extraction" approach rather than requirements gathering. The `questioning.md` reference defines this: you are a thinking partner, not an interviewer. Questions follow the thread of what the user emphasizes. The goal is helping the user sharpen a fuzzy idea into something concrete enough to build.

### Parallel Agent Safety

When multiple executors run in the same wave:
- Commits use `--no-verify` to prevent pre-commit hook lock contention (e.g., cargo lock fights in Rust)
- The orchestrator runs `git hook run pre-commit` once after each wave
- STATE.md writes use file-level locking with atomic `O_EXCL` creation and stale lock detection (10-second timeout with jitter)

### Model Profile Design Rationale

- **Opus for gsd-planner:** Planning involves architecture decisions and goal decomposition — this is where model quality has highest impact.
- **Sonnet for gsd-executor:** Executors follow explicit PLAN.md instructions. The reasoning is already done; execution is implementation.
- **Sonnet (not Haiku) for verifiers in balanced:** Verification requires goal-backward reasoning — checking if code *delivers* what the phase promised, not just pattern matching.
- **Haiku for gsd-codebase-mapper:** Read-only exploration and pattern extraction — no reasoning required, just structured output from file contents.

### Version Pinning Strategy

GSD returns `"inherit"` (not `"opus"`) for opus-tier agents. This is because Claude Code's `"opus"` alias maps to a specific model version that organizations may block while allowing newer versions. `"inherit"` causes agents to use whatever opus version the user has configured in their session.

### Decimal Phase Numbering

Urgent work inserted between phases uses decimal numbering (e.g., 3.1 inserted between phases 3 and 4). This avoids renumbering existing phases and their artifacts. The `decimal-phase-calculation.md` reference defines the algorithm.

### Seeds vs Backlog

- **Backlog** (999.x numbering): Ideas not ready for active planning. Get full phase directories immediately so `/gsd:discuss-phase 999.1` and `/gsd:plan-phase 999.1` work on them.
- **Seeds**: Forward-looking ideas with trigger conditions. Unlike backlog items, seeds surface automatically when `/gsd:new-milestone` scans them and finds milestone condition matches. Preserves the full WHY and WHEN context.

### Multi-Repo Workspace Support

For monorepos with separate git repos (e.g., `backend/`, `frontend/`, `shared/`), configure `planning.sub_repos` in config.json. GSD groups code files by their sub-repo prefix and commits each independently with the same message, while `.planning/` stays local.

---

## Security

GSD v1.27 introduced defense-in-depth security across multiple layers:

### Path Traversal Prevention
All user-supplied file paths (`--text-file`, `--prd`) are validated to resolve within the project directory. macOS `/var` → `/private/var` symlink resolution is handled in `security.cjs`.

### Prompt Injection Detection
The `security.cjs` module scans for known injection patterns (role overrides, instruction bypasses, system tag injections) in user-supplied text before it enters planning artifacts. Since GSD generates markdown files that become LLM system prompts, user-controlled text in planning artifacts is a potential indirect injection vector.

### Runtime Hook Guards
- `gsd-prompt-guard.js` — Active on every write to `.planning/`, advisory only, never blocks
- `gsd-workflow-guard.js` — Warns on file edits outside GSD workflow context (opt-in)

### CI Injection Scanner
`tests/prompt-injection-scan.test.cjs` scans all agent, workflow, and command files for embedded injection vectors. Runs as part of the test suite.

### Protecting Sensitive Files

Add sensitive file patterns to Claude Code's deny list in `.claude/settings.json`:

```json
{
  "permissions": {
    "deny": [
      "Read(.env)", "Read(.env.*)",
      "Read(**/secrets/*)", "Read(**/*credential*)",
      "Read(**/*.pem)", "Read(**/*.key)"
    ]
  }
}
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Commands not found after install | Restart runtime; verify files in `~/.claude/commands/gsd/` |
| Lost context / new session | `/gsd:resume-work` or `/gsd:progress` |
| Phase went wrong | `git revert` the phase commits, then re-plan |
| Plans seem wrong or misaligned | Run `/gsd:discuss-phase N` before planning; check `/gsd:list-phase-assumptions N` |
| Execution produces stubs | Plans too ambitious; re-plan with 2–3 tasks maximum |
| Context degradation during session | `/clear` then `/gsd:resume-work` |
| Model costs too high | `/gsd:set-profile budget`; toggle off research and plan_check via `/gsd:settings` |
| Non-Anthropic provider (OpenRouter, local) | `/gsd:set-profile inherit` to prevent direct Anthropic model calls |
| Parallel execution build errors | Update to latest GSD or set `parallelization.enabled: false` |
| GSD update overwrote local changes | `/gsd:reapply-patches` (patches backed up since v1.17) |
| Something broke | `/gsd:debug "description"` — scientific debugging with persistent state |
| Don't know what step is next | `/gsd:next` |
| Docker / containerized install path issues | Set `CLAUDE_CONFIG_DIR=/home/user/.claude` before running installer |
| Windows install crashes on protected directories | Fixed in v1.24+; temporarily rename the protected directory as workaround |
| Want session summary for stakeholders | `/gsd:session-report` |

---

*Documentation generated from `E:/Project/My Workflow/gsd/` (v1.27.0) on 2026-03-21.*
