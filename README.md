# AI Coding Workflow

A Claude Code framework that transforms AI-assisted development from ad-hoc prompting into a structured, repeatable engineering process. Built on an orchestrator + subagent architecture with 8 workflow commands, 7 specialized agents, quality gates, resumable state, and pattern reuse.

## Quick Start

1. Copy `.claude/` and `.workflow/` directories + `CLAUDE.md` into your project root
2. Edit `.workflow/config.json` — set `project_name` and project-specific settings
3. Run `/init` to scan your project and generate an overview
4. Plan work: `/plan "Add user export feature"`
5. Execute: `/execute`

## How It Works

```
/init ─── scan project ──► .workflow/project-overview.md (loaded every session)
                                      │
/plan ─── requirements ──► plan.json + phase files + state.json
  │         │                         │
  │    auto-discovers            /analyze
  │    matching templates        (fills knowledge gaps)
  │         │                         │
  │    /template-apply ──────────────►│
  │                                   │
  └── planner agent ── reviewer agent ─► approved plan
                                      │
/execute ──────────────────────► implementation
  │                                   │
  ├── executor agent (TDD per task)   │
  ├── reviewer agent (per phase)      │
  ├── state tracking via CLI          │
  └── /doc-update (final reconciliation)
                                      │
/template-create ◄────────── completed work
  │                          (extract pattern for reuse)
  └──► .workflow/templates/{name}/
```

## Workflow Commands

### `/init` — Initialize Project

Scans your project and generates `.workflow/project-overview.md` — a concise overview loaded every session so every agent understands your project.

```
/init
```

**What it captures:** Project type, tech stack, system architecture, project structure, modules, 3-5 core user flows (trigger, steps, input/output, side effects), data model with ER diagram, external integrations, patterns, testing setup, build/deploy pipeline.

**Output:** `project-overview.md` with mandatory Mermaid diagrams (system context, architecture, data flow, ER). Max ~4k tokens. Adaptive — omits sections that don't apply.

### `/plan` — Create Execution Plan

Transforms requirements into a phased, dependency-aware execution plan with automated quality review.

```
/plan "Add user export feature"
/plan ./requirements/export.md
/plan gh:123
/plan jira:PROJ-456
```

**Flow:**
1. Parse requirements (text, file, GitHub issue, or Jira ticket)
2. Auto-discover matching templates from `.workflow/templates/`
3. Clarify ambiguities with user (max 3 rounds)
4. Analyze affected components — triggers `/analyze` for missing/stale docs
   - Modified/Extended components: deep analysis (recursive)
   - Consumed/Created components: shallow analysis
   - Verification gate: confirms all `.analysis.md` files exist before proceeding
5. Planner agent creates phased plan with dependency graph
6. Reviewer agent checks 8 quality dimensions
7. User review and approval

**Output:** `.workflow/plans/{date}-{name}/` with `plan.json`, `phase-{N}.json`, `state.json`

**8 Review Dimensions:** Requirement coverage, task atomicity, dependency correctness, file scope safety (parallel phases can't touch same files), acceptance criteria completeness, test coverage mapping, consistency, codebase alignment.

### `/execute` — Execute Plan

Implements the approved plan phase-by-phase with TDD, code review, and state tracking.

```
/execute                    # latest approved plan
/execute {plan-path}        # specific plan
/execute --resume           # continue interrupted work
```

**Per task:** TDD (write failing test → implement → pass test) → update state via CLI

**Per phase:** Code review (reviewer agent) → Playwright check (if UI) → regression tests

**After all phases:** Final reconciliation — single doc-update pass using full git diff from execution start. Each component assessed once, not per-phase.

**State management:** All reads/writes through `workflow_cli.py`. Atomic updates, no markdown parsing, supports parallel execution without conflicts.

**Resume:** Sessions can interrupt at any point. Run `/execute --resume` to continue from the exact substep where work stopped.

### `/analyze` — Component Analysis

Deep analysis of a specific component. Produces co-located documentation capturing hidden knowledge, integration patterns, and gotchas.

```
/analyze src/services/authService.ts
/analyze src/modules/auth --recursive
```

**Modes:**
| Mode | When | Model | Scope |
|------|------|-------|-------|
| Full | First-time analysis | Opus | Complete from scratch |
| Update | Code changed since last analysis | Sonnet | Incremental — only changed sections |
| Recursive | `--recursive` flag | Opus/Sonnet | Component + all dependencies (leaf → top) |

**Staleness detection:** Automatic via `last_commit` in frontmatter vs `git log`. No manual tracking needed.

**Alias resolution:** Handles `@/`, `~/`, `#/` path aliases by reading tsconfig/vite/webpack config. Aliased imports are treated as local dependencies.

**Recursive chain guarantee:** C analyzed first → B analyzed next (with C's docs) → A analyzed last (with B's and C's docs). Each level has full dependency context.

**Output:** `{ComponentName}.analysis.md` alongside the source file, with progressive loading markers:
- Level 0: Frontmatter only (~50 tokens) — for scanning
- Level 1: + Content section (~300-500 tokens) — for interacting with the component
- Level 2: Full document (~500-800 tokens) — for modifying the component

### `/template-create` — Extract Pattern

Extracts a repeatable implementation pattern from completed work into a reusable template.

```
/template-create payment-provider
```

**Source options (prioritized):**
1. **From completed execution** (richest) — auto-detects recently completed plans, loads plan intent, git diff, affected components, analysis docs, and task structure
2. **From git history** — branch diff or commit range
3. **From existing code** — file paths or component path
4. **Mixed** — any combination

**Variability markers per section:**
| Marker | Meaning | Example |
|--------|---------|---------|
| `[F]` Fixed | Copy as-is every time | Error handling wrapper, config registration |
| `[P]` Parametric | Same structure, swap values | API paths, column definitions, component names |
| `[G]` Guided | Follow the shape, expect differences | Vendor-specific UI, custom validation logic |

**Abstraction technique:** The template-extractor agent uses multi-case reasoning — imagines 2-3 variant scenarios to find what's truly fixed vs parametric vs guided. What's common across all imagined variants is the pattern.

### `/template-apply` — Use Template

Applies an existing template to accelerate a new implementation.

```
/template-apply payment-provider
```

**Flow:** Load template → collect variable values → for `[G]` sections ask user for details → generate plan (recommended if `[G]` sections exist) or task list (only if all `[F]`/`[P]`).

**Auto-discovery:** When you run `/plan`, it checks `.workflow/templates/index.md` for keyword matches and suggests relevant templates automatically.

### `/doc-update` — Update Documentation

Assesses code change significance and applies the right level of documentation update.

```
/doc-update
```

Usually called automatically by `/execute` during final reconciliation. Can also be run manually.

**Classification:**
| Level | Action | Example |
|-------|--------|---------|
| NO UPDATE | Skip | Typo fix, log message, dep bump |
| MINOR | Patch inline | New field, new prop, new endpoint |
| MAJOR | Trigger `/analyze` | Data flow changed, API contract changed |

**Handles missing docs:** If `.analysis.md` doesn't exist (new component or missed during planning), triggers full `/analyze` automatically.

### `/jira` — Fetch Jira Ticket

Fetches a Jira ticket and transforms ADF content to clean markdown for planning.

```
/jira PROJ-456
```

Requires `jira_fetch.py` setup and `JIRA_TOKEN` environment variable. Configure in `.workflow/config.json`.

## Architecture

### Two-Layer Design

```
Skills (.claude/skills/)              Agents (.claude/agents/)
├── Orchestration                     ├── Domain expertise
├── Input parsing                     ├── Reasoning approach
├── Cross-function calls              ├── Decision framework
├── Output format + verification      ├── Quality standards
└── User interaction                  └── Anti-patterns to avoid
```

**Skills own WHAT/WHERE/WHEN.** They define the workflow: parse input, determine which steps to run, what context to give the agent, what format the output should be, how to verify results.

**Agents own HOW to think.** They bring domain expertise: how to read code, how to assess significance, how to decompose requirements, when to escalate vs decide.

**Why this split:** Skills run in the main session (can cross-call skills + spawn agents). Agents run as subagents (can invoke skills but cannot spawn other agents). The main session is the natural orchestrator.

### Agents

| Agent | Model | Role |
|-------|-------|------|
| **planner** | Opus | Designs phased plans from requirements |
| **executor** | Sonnet | Implements one task with TDD |
| **analyzer** | Opus | Deep component analysis |
| **reviewer** | Sonnet | Quality gate (8-dimension plan review + code review) |
| **doc-updater** | Sonnet | Change significance assessment |
| **template-extractor** | Opus | Pattern abstraction via multi-case reasoning |
| **template-applier** | Sonnet | Variable substitution + plan generation |

**Cost optimization:** Opus for tasks requiring synthesis and judgment (planning, analysis, pattern extraction). Sonnet for mechanical or checklist-based tasks (execution, review, doc updates).

### State Management

Plan, phase, and state data stored as JSON. All reads/writes go through `workflow_cli.py`:

```bash
# Read
python .claude/scripts/workflow_cli.py state current       # ~20 tokens in context
python .claude/scripts/workflow_cli.py phase tasks 2       # just the task list
python .claude/scripts/workflow_cli.py plan show            # readable summary

# Write
python .claude/scripts/workflow_cli.py state complete-task 1 task-01
python .claude/scripts/workflow_cli.py state start-phase 2
python .claude/scripts/workflow_cli.py state log "Phase 1 completed"
```

**Why JSON + CLI instead of markdown:**
- Token efficient — read one field (~20 tokens) instead of full file (~300+ tokens)
- Reliable — atomic structured writes, no string-matching edits
- Fast — no markdown parsing, no frontmatter extraction
- Parallel-safe — CLI does read-modify-write atomically

## Quality System

### Three Layers

**Layer 1: General rules** (`.claude/rules/`, always loaded)
- `quality-criteria.md` — Type safety, error handling, security, testing, code hygiene
- `tdd-policy.md` — Pragmatic TDD with documented exceptions
- `security-gates.md` — Blocked commands + confirmation gates

**Layer 2: Project-specific rules** (`.workflow/rules/`)
- `planning/` — Rules for plan review (loaded by reviewer during planning)
- `code/` — Rules for code review (loaded by reviewer during execution)

Each rule file: Rule statement, Why it exists, Correct example, Incorrect example, Exceptions.

**Layer 3: Plan-specific criteria** — Acceptance criteria per task, verified during phase review.

### Hooks

| Hook | When | What |
|------|------|------|
| **Security gate** | Before Bash/Write/Edit | Blocks catastrophic commands, asks confirmation for risky ones |
| **Quality check** | After Write/Edit | Warns about debug output, empty catches, undescribed TODOs |
| **Context monitor** | After every tool use | Warns at 35% remaining, critical at 25%, stops at 15% |

## Configuration

### `.workflow/config.json`

```json
{
  "project_name": "my-app",
  "tdd_policy": "pragmatic",
  "tdd_exceptions": ["UI layout/styling", "config files", "type definitions"],
  "playwright_check": true,
  "auto_commit": false,
  "model_overrides": {
    "planner": "opus",
    "executor": "sonnet",
    "reviewer": "sonnet",
    "analyzer": "opus",
    "analyzer_update": "sonnet",
    "doc_updater": "sonnet",
    "template_extractor": "opus",
    "template_applier": "sonnet"
  },
  "jira": {
    "base_url": "https://yourorg.atlassian.net",
    "auth_env_var": "JIRA_TOKEN",
    "default_project": "PROJ"
  }
}
```

### Project-Specific Rules

Drop `.md` files in `.workflow/rules/planning/` or `.workflow/rules/code/`:

```markdown
---
name: Mutation Pattern
---

## Rule
All data mutations must use Server Actions, not API route handlers.

## Why
Server Actions provide automatic form handling and type-safe contracts.

## Correct
Server action with 'use server' directive, direct database call.

## Incorrect
API route handler with POST, client-side fetch call.

## Exceptions
- Webhook endpoints (must be API routes by nature)
```

## Directory Structure

```
.claude/
├── skills/                  # Workflow commands (8)
│   ├── init/SKILL.md
│   ├── plan/SKILL.md
│   ├── execute/SKILL.md
│   ├── analyze/SKILL.md
│   ├── template-create/SKILL.md
│   ├── template-apply/SKILL.md
│   ├── doc-update/SKILL.md
│   └── jira/SKILL.md
├── agents/                  # Specialized workers (7)
│   ├── planner.md
│   ├── executor.md
│   ├── analyzer.md
│   ├── reviewer.md
│   ├── doc-updater.md
│   ├── template-extractor.md
│   └── template-applier.md
├── scripts/
│   └── workflow_cli.py      # Plan/phase/state JSON CLI
├── rules/                   # Always-loaded quality rules
│   ├── quality-criteria.md
│   ├── tdd-policy.md
│   ├── security-gates.md
│   └── resume-protocol.md
├── hooks/                   # Lifecycle hooks
│   ├── pre_tool_use.py
│   ├── post_tool_use.py
│   └── context_monitor.py
└── settings.json            # Hook registration

.workflow/
├── config.json              # Project configuration
├── project-overview.md      # Generated by /init
├── rules/                   # Project-specific quality rules
│   ├── planning/
│   └── code/
├── templates/               # Reusable patterns
│   ├── index.md
│   └── {name}/
│       ├── template.md
│       └── references/
└── plans/                   # Execution history
    └── {date}-{name}/
        ├── plan.json
        ├── phase-{N}.json
        └── state.json

Component docs (co-located with source):
  src/services/authService.analysis.md
  src/components/Dashboard.analysis.md
  src/modules/auth/auth.analysis.md
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Skill + Agent two-layer (not three) | Skills can cross-call via Skill tool. No need for intermediate "procedures" layer. |
| Skills own orchestration, agents own thinking | Agent doesn't inherit skill content. Skill defines the contract, agent brings expertise. |
| JSON + CLI for state (not markdown) | Token efficient, atomic writes, parallel-safe, no format drift. |
| Doc updates at end, not per-phase | Avoids redundant updates when multiple phases touch same component. One assessment per component. |
| Deep analysis for modified/extended, shallow for consumed/created | Deep recursive analysis can cascade to half the codebase. Consumed components only need the API contract. |
| Artifact verification gates | AI agents skip `/analyze` when source is already in context. Check that `.analysis.md` exists on disk, not that the agent followed the instruction. |
| Component docs co-located with source | Path IS the namespace (no naming collisions). Same pattern as `.test.tsx`. Git-friendly. |
| Opus for planning/analysis, Sonnet for execution/review | Synthesis tasks need Opus. Mechanical tasks run fine on Sonnet at 1/5 the cost. |
| Pragmatic TDD | Tests first by default. Documented exceptions for UI, config, types. Not dogmatic. |
| Template variability markers | Per-section `[F]`/`[P]`/`[G]` handles the spectrum from cookie-cutter to structurally different. |
| Multi-case reasoning for template extraction | Imagining variants reveals true abstraction. What survives across all imagined cases is the pattern. |
