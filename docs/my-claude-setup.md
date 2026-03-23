# my-claude-setup — AI Workflow Framework Documentation

> Last updated: 2026-03-21
> Framework version: v7.0 (Full Solo Architecture)
> Source: `E:/Project/My Workflow/my-claude-setup/`

---

## Table of Contents

- [Overview / Purpose](#overview--purpose)
- [Key Features](#key-features)
- [Folder Structure](#folder-structure)
- [Core Components](#core-components)
  - [CLAUDE.md — Main Context File](#claudemd--main-context-file)
  - [settings.json — Hook Configuration](#settingsjson--hook-configuration)
  - [Hooks System](#hooks-system)
  - [Skills System](#skills-system)
  - [Agents System](#agents-system)
  - [Rules System](#rules-system)
  - [MCP Servers](#mcp-servers)
- [How It Works](#how-it-works)
  - [Development Pipeline](#development-pipeline)
  - [Quality Gate System](#quality-gate-system)
  - [Hook Event Lifecycle](#hook-event-lifecycle)
  - [Session Management](#session-management)
  - [Security Gating](#security-gating)
- [Usage Guide](#usage-guide)
  - [Prerequisites](#prerequisites)
  - [Installation — Option A: Symlink (Recommended)](#installation--option-a-symlink-recommended)
  - [Installation — Option B: Copy Per-Project](#installation--option-b-copy-per-project)
  - [Initial Configuration with /customize](#initial-configuration-with-customize)
  - [Daily Usage Patterns](#daily-usage-patterns)
  - [Running Tests](#running-tests)
  - [Troubleshooting](#troubleshooting)
- [Notable Patterns and Design Decisions](#notable-patterns-and-design-decisions)
- [Future Enhancements](#future-enhancements)

---

## Overview / Purpose

`my-claude-setup` is a **production-ready Claude Code configuration layer** extracted from a real SaaS codebase and generalized for reuse. It is not an application — it is tooling infrastructure that sits on top of [Claude Code](https://docs.anthropic.com/en/docs/claude-code), the Anthropic CLI.

The framework is purpose-built for **Next.js / Supabase / TypeScript** projects and provides:

- **Automated quality gates** that fire on every file write, catching bugs and convention violations at write-time rather than at code review
- **Guided development workflows** as slash commands (`/create-plan`, `/implement`, `/dev`, etc.)
- **Specialized sub-agents** for architecture, security, testing, and documentation tasks
- **Security blocks** that prevent catastrophic commands (database resets, force pushes, credential staging) before they execute
- **MCP server integrations** for browser automation, documentation lookup, web search, diagramming, and structured reasoning
- **Coding rules** loaded as passive context, enforcing TypeScript, React, Supabase, and security standards on every session

The primary value is the **structured development pipeline**: `/create-plan → /audit-plan → /review-plan → /implement`. This pipeline enforces planning, structural review, quality gating, and TDD before any code is written, preventing the hours of rework that come from building on wrong assumptions.

As of **v7.0 (March 2026)**, the architecture moved from a subagent-team model to a **solo session model**: every skill runs inline in one Claude Code session with the full 1M context window. Subagents are no longer spawned for planning or implementation — the user opens multiple terminal sessions manually to parallelize work across plan groups.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **14 Hook scripts** | Python scripts that run at Claude Code lifecycle events (session start/end, before/after tool use, on task completion, etc.) |
| **23 Skill slash commands** | Guided workflows invoked as `/skill-name`, covering planning, building, reviewing, and MCP tool usage |
| **5 Specialized agents** | Sub-agent definitions for architecture, code quality, security, TDD, and documentation |
| **5 MCP server integrations** | Playwright, Context7, Tavily, Sequential Thinking, Draw.io |
| **16 Coding rules** | Markdown files loaded as passive context covering TypeScript, React, Supabase, security, testing, git workflow, and more |
| **Tiered security blocking** | Three preset command-blocking tiers (lax, normal, strict) plus custom rules — all regex-driven |
| **Automatic MCP cleanup** | Orphaned MCP server processes are detected and killed on session start using process-tree ancestry |
| **Structured JSONL logging** | All hook events are appended to a single `hooks.jsonl` file, grep-able across sessions |
| **TypeScript quality checks** | Two-layer regex checks on every `.ts`/`.tsx` write catch `any` types, missing `server-only`, hardcoded secrets, and more |
| **TDD enforcement** | `TaskCompleted` hook blocks task completion with a role-specific checklist, requiring tests and verification before signoff |
| **Customization wizard** | `/customize` onboarding skill fills all `<!-- CUSTOMIZE -->` markers across `CLAUDE.md` and rule files automatically |

---

## Folder Structure

```text
my-claude-setup/
├── .claude/
│   ├── agents/                         # 5 specialized sub-agent definitions
│   │   ├── architect.md
│   │   ├── code-quality-reviewer.md
│   │   ├── doc-updater.md
│   │   ├── security-reviewer.md
│   │   └── tdd-guide.md
│   │
│   ├── hooks/                          # 14 Python hook scripts + utilities
│   │   ├── config/
│   │   │   ├── blocked-commands.json   # Active tier selector + custom rules
│   │   │   ├── project-checks.json     # Project-specific TypeScript validator config
│   │   │   ├── quality-check-excludes.json  # Paths excluded from quality checks
│   │   │   └── tiers/
│   │   │       ├── lax.json            # Minimal blocking (catastrophic only)
│   │   │       ├── normal.json         # Default (catastrophic + git safety + SQL)
│   │   │       └── strict.json         # Maximum blocking (adds systemctl, ssh-keygen, etc.)
│   │   ├── utils/
│   │   │   ├── constants.py            # Shared paths, JSONL logging helper
│   │   │   ├── log_cleanup.py          # Rotates logs at 5MB, prunes sessions >30 days
│   │   │   ├── mcp_cleanup.py          # Discovers and kills orphaned MCP processes
│   │   │   ├── mcp_health.py           # Checks MCP binary availability
│   │   │   └── notify.py               # Sound notification via HTTP
│   │   ├── validators/
│   │   │   ├── typescript_validator.py # Project-specific TS pattern checks
│   │   │   ├── validate_file_contains.py    # Asserts file contains required sections
│   │   │   ├── validate_new_file.py         # Asserts a new file was created
│   │   │   ├── validate_no_placeholders.py  # Detects skeleton/placeholder content
│   │   │   └── validate_tdd_tasks.py        # Enforces TDD ordering in phase files
│   │   ├── instructions_loaded.py      # Logs which rules load per session
│   │   ├── notification.py             # Plays sound on permission prompts
│   │   ├── post_tool_use.py            # Quality checks after Write/Edit on TS files
│   │   ├── post_tool_use_failure.py    # Actionable guidance after tool failures
│   │   ├── pre_compact.py              # Backs up transcript before context compaction
│   │   ├── pre_tool_use.py             # Blocks dangerous commands; logs all tool calls
│   │   ├── session_end.py              # Kills THIS session's MCP servers; logs end
│   │   ├── session_start.py            # Kills orphaned MCP servers; injects git context
│   │   ├── stop.py                     # Exports transcript to chat.json; plays completion sound
│   │   ├── stop_task_check.py          # Catches orphaned in_progress tasks at turn end
│   │   ├── task_completed.py           # Verification gate on task completion (deduped)
│   │   ├── teammate_idle.py            # Logs teammate idle events
│   │   └── user_prompt_submit.py       # Logs prompts; stores for status display
│   │
│   ├── skills/                         # 23 skill directories (each with SKILL.md)
│   │   ├── audit-plan/                 # Structural flow audit for multi-phase plans
│   │   ├── cache-audit/                # Caching strategy review
│   │   ├── code-review/                # Post-implementation code quality review
│   │   ├── context7-mcp/               # Context7 documentation lookup wrapper
│   │   ├── customize/                  # Onboarding wizard — fills CUSTOMIZE markers
│   │   ├── create-plan/                # Creates phased implementation plans
│   │   │   └── references/
│   │   │       ├── PLAN-TEMPLATE.md    # Canonical plan.md template
│   │   │       └── PHASE-TEMPLATE.md   # Canonical phase file template
│   │   ├── dev/                        # Ad-hoc development workflow
│   │   ├── drawio-mcp/                 # Draw.io diagram creation wrapper
│   │   ├── implement/                  # Implements a plan group (solo session)
│   │   ├── improve-prompt/             # Prompt improvement helper
│   │   ├── playwright-e2e/             # E2E test authoring with Playwright
│   │   ├── playwright-mcp/             # Playwright MCP browser automation wrapper
│   │   ├── postgres-expert/            # PostgreSQL/Supabase schema and RLS expert
│   │   ├── react-form-builder/         # React forms with react-hook-form + Zod
│   │   ├── review-plan/                # Template + codebase compliance review (one file)
│   │   ├── sequential-thinking-mcp/    # Sequential Thinking MCP wrapper
│   │   ├── server-action-builder/      # Next.js Server Actions with auth + Zod
│   │   ├── service-builder/            # Service layer (private class + factory)
│   │   ├── tavily-mcp/                 # Tavily web search wrapper
│   │   ├── vercel-composition-patterns/ # React composition patterns (57 rules)
│   │   ├── vercel-react-best-practices/ # React/Next.js performance patterns
│   │   ├── vercel-react-native-skills/  # React Native / Expo patterns
│   │   └── web-design-guidelines/      # UI/UX design review
│   │
│   ├── settings.json                   # Hook bindings to Claude Code lifecycle events
│   └── settings.local.json.example    # Template for per-developer overrides
│
├── rules/                              # 16 coding rule files (symlinked to ~/.claude/rules/)
│   ├── admin.md                        # Admin operations guidelines
│   ├── coding-style.md                 # TypeScript/React coding standards
│   ├── database.md                     # Supabase/Postgres patterns and RLS
│   ├── date-formatting.md              # Date parsing (YYYY-MM-DD as local time)
│   ├── domain-patterns.md              # Compressed critical patterns — alwaysApply: true
│   ├── forms.md                        # Form handling with react-hook-form + Zod
│   ├── git-workflow.md                 # Branch strategy and commit conventions
│   ├── i18n.md                         # Internationalization patterns
│   ├── mcp-tools.md                    # MCP server usage guide
│   ├── pages-and-layouts.md            # Next.js page/layout conventions
│   ├── patterns.md                     # Data fetching, mutations, service patterns
│   ├── pre-implementation-analysis.md  # Blast radius, security, and pattern checks
│   ├── route-handlers.md               # API route handler conventions
│   ├── security.md                     # RLS, secrets, auth, multi-tenant isolation
│   ├── testing.md                      # Vitest, mocking, TDD workflow
│   └── ui-components.md                # Component library usage guidelines
│
├── tests/
│   └── hooks/
│       ├── conftest.py                 # Test helpers: run_hook(), input builders
│       ├── run_tests.py                # Standalone test runner (uv run --script)
│       ├── test_post_tool_use.py       # Quality gate tests
│       ├── test_pre_tool_use.py        # Security gate tests
│       └── test_typescript_validator.py # TypeScript validator tests
│
├── docs/
│   ├── workflow.md                     # Historical pre-v7 subagent architecture
│   ├── setup-review-2026-03-03.md      # Full configuration review
│   ├── future-enhancements.md          # Deferred improvement items
│   ├── pipeline.png / .svg / .drawio   # Pipeline diagram
│   └── research/                       # Research documents (Vercel skills evals, etc.)
│
├── .github/
│   └── workflows/
│       └── claude.yml                  # GitHub Actions: trigger Claude on @claude mentions
│
├── .mcp.json.example                   # Example MCP server config (copy + add API keys)
├── .gitignore
├── CLAUDE.md                           # Main project instructions loaded by Claude Code
├── LICENSE
├── plugins.md                          # Optional LSP plugin documentation
└── README.md                           # Full setup guide
```

---

## Core Components

### CLAUDE.md — Main Context File

**Path:** `my-claude-setup/CLAUDE.md`

`CLAUDE.md` is the primary instruction file loaded by Claude Code at the start of every session. It defines:

- **Critical Rules** — Ten high-impact guardrails derived from real production mistakes (e.g., never use `any`, use proper logger, always `await params`, validate Server Actions with Zod)
- **Architecture** — The four-stage development pipeline and its quality gates
- **Component Inventory** — A table of all hooks, skills, agents, rules, and MCP servers
- **Deployment model** — How skills/agents/rules are symlinked vs copied
- **Code style summary** — Key TypeScript and React patterns

The file uses `<!-- CUSTOMIZE -->` markers throughout. Before using this setup on a new project, run `/customize` to fill these markers with project-specific details (project name, commands, component library, auth model, etc.).

---

### settings.json — Hook Configuration

**Path:** `my-claude-setup/.claude/settings.json`

This JSON file binds Python hook scripts to Claude Code's lifecycle events. Every hook is invoked via `uv run $CLAUDE_PROJECT_DIR/.claude/hooks/<script>.py` with a 10-second timeout.

Key settings:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "in-process",
  "companyAnnouncements": [
    "Pipeline: /create-plan → /audit-plan → /review-plan → /implement | Ad-hoc: /dev"
  ]
}
```

The `companyAnnouncements` field injects the pipeline reminder into every session's startup context. The `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` env var enables the team/agent features even in solo mode.

A `settings.local.json` (gitignored) can override any setting per-developer — useful for disabling hooks during debugging (`"disableAllHooks": true`).

---

### Hooks System

All hooks are Python 3.11+ scripts with zero external dependencies (stdlib only), executed via `uv run --script`. They communicate via JSON on stdin/stdout using the Claude Code hook protocol.

#### Hook Event Map

| Event | Script | What It Does |
|-------|--------|--------------|
| `PreToolUse` | `pre_tool_use.py` | Intercepts Bash commands, checks against blocked-commands.json, blocks or asks for confirmation. Logs every tool call as JSONL. |
| `PostToolUse` | `post_tool_use.py` | After Write/Edit on `.ts`/`.tsx` files, runs 5 quality checks and injects warnings via `additionalContext`. Also trims oversized MCP outputs (>15,000 chars). |
| `PostToolUse` | `typescript_validator.py` | Project-specific TypeScript checks: `any` types, hardcoded secrets, admin client misuse, and config-driven checks (blocked imports, wrapper enforcement, naming conventions). |
| `PostToolUseFailure` | `post_tool_use_failure.py` | Pattern-matches error messages and injects actionable guidance (e.g., "Read file before Edit"). |
| `Notification` | `notification.py` | Plays a sound when Claude needs user input (permission prompts). Ignores idle/auth events. |
| `Stop` | `stop.py` | Exports JSONL transcript to `chat.json`. Plays completion sound. |
| `Stop` | `stop_task_check.py` | Detects orphaned `in_progress` tasks via a marker file handshake with `task_completed.py`. Injects a reminder to close them. |
| `PreCompact` | `pre_compact.py` | Logs context compaction events. Optionally backs up the transcript before compression. |
| `UserPromptSubmit` | `user_prompt_submit.py` | Logs prompt metadata and stores prompt text for status display. |
| `SessionStart` | `session_start.py` | Kills MCP orphans from previous crashes. Injects git branch + dirty file count as context. Runs log cleanup and MCP health checks. |
| `SessionEnd` | `session_end.py` | Kills only THIS session's MCP server processes (identified via process-tree ancestry). Logs end reason. |
| `TaskCompleted` | `task_completed.py` | Blocks first completion attempt with a role-specific verification reminder (builder/validator/auditor/planner). Allows retry. Rate-limited to break loops. |
| `TeammateIdle` | `teammate_idle.py` | Logs teammate idle events for debugging agent lifecycle. |
| `InstructionsLoaded` | `instructions_loaded.py` | Logs which rules and instructions load per session. |

#### Two-Layer TypeScript Quality Checks

The post-write quality system uses two hooks with a clean separation of responsibility to prevent duplicate warnings:

| Hook | Owns |
|------|------|
| `post_tool_use.py` | Generic: `console.log`/`console.error`, missing `import 'server-only'`, missing `'use client'`, default exports in component files |
| `typescript_validator.py` | TypeScript-specific: `: any` types, hardcoded secrets, admin client misuse, project-specific import patterns |

Both hooks read `.claude/hooks/config/project-checks.json` for project-specific configuration. When the file is absent, only generic/universal checks run.

#### Security Blocking — Tiered System

`pre_tool_use.py` loads rules from `.claude/hooks/config/blocked-commands.json`, which selects a tier and can add custom rules:

```json
{ "tier": "normal", "additional_rules": [] }
```

Three preset tiers are available in `.claude/hooks/config/tiers/`:

- **lax.json** — Blocks only catastrophic irreversible operations (DROP DATABASE, force push, curl-to-shell)
- **normal.json** — Adds git safety blocks (checkout, reset, rebase, clean, merge), SQL confirmation prompts, Docker volume protection, and selective `git add -A` prompting
- **strict.json** — Adds everything from normal plus systemctl, ssh-keygen, recursive chmod/chown, killall, and mv against project directories

Each rule has:
- `pattern` — regex matched against the normalized command
- `safe_patterns` — regex exceptions (e.g., `DELETE FROM` is fine if it includes `WHERE`)
- `action` — `"deny"` (hard block) or `"ask"` (user confirmation required)
- `reason` — explanation injected into Claude's context

---

### Skills System

Skills are slash commands that load a `SKILL.md` file as a structured prompt, giving Claude a step-by-step workflow to follow. Each skill lives in `.claude/skills/<skill-name>/SKILL.md`.

#### Planning Skills (Core Pipeline)

| Skill | Purpose | Key Behavior |
|-------|---------|--------------|
| `/create-plan` | Creates phased implementation plans | Solo session: clarifies requirements, explores codebase, reads templates, creates plan.md + phase files, self-reviews. Two user checkpoints for course-correction. |
| `/audit-plan` | Structural flow audit | Analyzes ALL phases as a whole for dependency ordering, data flow consistency, circular deps. Runs BEFORE per-phase reviews. Can bail out with "Unusable" verdict. |
| `/review-plan` | Per-file template + codebase compliance review | Reviews ONE file per invocation (plan.md OR a single phase). Grounds findings in real codebase files. Auto-fixes Critical/High/Medium issues. |
| `/implement` | Implements one plan group | Solo session with full 1M context. Reads entire plan, implements assigned group's phases with TDD, self code-review, and Playwright smoke check. |
| `/dev` | Ad-hoc development | Implements features/fixes directly without a formal plan. Routes to domain skills automatically. Confirms scope via `git diff` before reporting done. |

#### Domain Skills (Invoked by /dev and /implement)

| Skill | Domain | When Used |
|-------|--------|-----------|
| `/postgres-expert` | Database schemas, RLS, migrations | Any database work — tables, policies, migrations, SQL functions |
| `/server-action-builder` | Next.js Server Actions | Creating mutations with Zod validation and auth checks |
| `/service-builder` | Service layer | Private class + factory function business logic |
| `/react-form-builder` | React forms | react-hook-form + Zod form components |
| `/vercel-react-best-practices` | React/Next.js performance | Components, pages, bundle optimization (57 rules) |
| `/vercel-composition-patterns` | React architecture | Compound components, variant patterns, context interfaces |
| `/vercel-react-native-skills` | React Native/Expo | Mobile-specific patterns, list performance, animations |
| `/playwright-e2e` | E2E test authoring | Writing Playwright test specs |
| `/web-design-guidelines` | UI/UX review | Design quality and guideline compliance |

#### Code Quality Skills

| Skill | Purpose |
|-------|---------|
| `/code-review` | Post-implementation review: grounds findings in real codebase files, checks against 451-line checklist, auto-fixes Critical/High issues |
| `/cache-audit` | Reviews caching strategy |
| `/improve-prompt` | Improves a prompt's clarity and effectiveness |

#### Utility Skills

| Skill | Purpose |
|-------|---------|
| `/customize` | Onboarding wizard — collects project info and fills all CUSTOMIZE markers |
| `/context7-mcp` | Context7 documentation lookup |
| `/tavily-mcp` | Tavily web search |
| `/playwright-mcp` | Playwright browser automation |
| `/drawio-mcp` | Draw.io diagram creation |
| `/sequential-thinking-mcp` | Structured step-by-step reasoning |

#### Skill Anatomy

A typical skill directory looks like:

```
skills/code-review/
├── SKILL.md              # Main instruction file (always required)
├── checklist.md          # Detailed checklist referenced by the skill
├── references/
│   └── CODE-REVIEW-TEMPLATE.md   # Output template
└── scripts/
    └── validate_review.py        # Deterministic post-write validator
```

Skills can define their own per-invocation hooks in frontmatter:
```yaml
hooks:
  PostToolUse:
    - matcher: "Write"
      command: "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/validators/validate_file_contains.py"
```

---

### Agents System

Agents are sub-agents that Claude Code can delegate tasks to via the `Task` tool. Each agent definition is a markdown file in `.claude/agents/` with YAML frontmatter specifying tools, model, permission mode, and color.

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| `architect` | sonnet | Read, Grep, Glob | Architecture design and trade-off analysis. Read-only (`plan` permission mode). Analyzes schemas, route structures, service boundaries. |
| `code-quality-reviewer` | sonnet | Read, Grep, Glob, Bash | TypeScript/React pattern compliance review. Uses the `/code-review` skill. |
| `doc-updater` | sonnet | Read, Write, Edit, Bash, Grep, Glob | Updates CLAUDE.md, architecture maps, and guides after feature implementations. |
| `security-reviewer` | sonnet | Read, Write, Edit, Bash, Grep, Glob | RLS policy validation, secrets detection, OWASP Top 10 scanning, multi-tenant isolation checks. |
| `tdd-guide` | sonnet | Read, Write, Edit, Bash, Grep | TDD specialist using Vitest + happy-dom. RED-GREEN-REFACTOR workflow, Supabase mock patterns, vi.hoisted(). |

Each agent has an explicit `description` with trigger phrases (`"design the schema"`, `"audit RLS policies"`, `"TDD this feature"`) so Claude auto-selects the appropriate agent without user instruction.

---

### Rules System

Rules are markdown files in `rules/` (at the repo root) that are symlinked to `~/.claude/rules/`. They load as passive context on every Claude Code session — no invocation required.

The special file `rules/domain-patterns.md` carries `alwaysApply: true` in its frontmatter and compresses critical patterns from all domain skills into ~6.8KB. This ensures pattern compliance even when a skill is not explicitly invoked (Vercel evaluations showed passive context achieves 100% compliance vs 53-79% for on-demand invocation).

**Rules inventory:**

| Rule File | Coverage |
|-----------|----------|
| `admin.md` | Admin operations and elevated privilege patterns |
| `coding-style.md` | TypeScript interfaces over types, immutability, service factory pattern, destructuring |
| `database.md` | Supabase migration commands, RLS policy patterns, helper functions |
| `date-formatting.md` | Parse YYYY-MM-DD strings as local time, not UTC (common timezone bug) |
| `domain-patterns.md` | Compressed patterns from all domain skills — always loaded |
| `forms.md` | react-hook-form + Zod, form component imports, Server Action submission |
| `git-workflow.md` | Branch strategy, commit conventions, remote configuration |
| `i18n.md` | next-intl or react-i18next patterns, translation namespaces |
| `mcp-tools.md` | How to use each MCP server (Playwright, Context7, Tavily, etc.) |
| `pages-and-layouts.md` | Next.js App Router page and layout conventions |
| `patterns.md` | Data fetching via loaders, mutation via Server Actions, service pattern |
| `pre-implementation-analysis.md` | Blast radius check, security review, pattern lookup before writing code |
| `route-handlers.md` | API route conventions, auth patterns, error handling |
| `security.md` | RLS mandatory, secret management, multi-tenant isolation |
| `testing.md` | Vitest with happy-dom, test directory structure, TDD workflow |
| `ui-components.md` | Component library usage, don't build custom when shared exists |

---

### MCP Servers

Five MCP servers are configured at user level in `~/.claude.json`. Example configuration is in `.mcp.json.example`.

| Server | Package | Purpose |
|--------|---------|---------|
| `playwright` | `@playwright/mcp@latest` | Browser automation: navigate pages, click, fill forms, screenshot. Used for Playwright smoke checks after implementation. |
| `context7` | `@upstash/context7-mcp` | Documentation lookup for libraries and frameworks. Requires `CONTEXT7_API_KEY`. |
| `tavily` | `tavily-mcp@latest` | Web search with structured results. Requires `TAVILY_API_KEY`. |
| `sequential-thinking` | `@modelcontextprotocol/server-sequential-thinking` | Structured step-by-step reasoning with branching and revision. |
| `drawio` | `@next-ai-drawio/mcp-server@latest` | Creates and edits Draw.io diagrams programmatically. |

---

## How It Works

### Development Pipeline

The primary workflow follows a four-stage pipeline:

```
/create-plan → /audit-plan → /review-plan → /implement
```

**Stage 1: `/create-plan [feature-name]`**
A solo session that: (1) clarifies requirements via `AskUserQuestion`, (2) explores the codebase with Glob/Grep/Read to ground the plan in real code, (3) reads `PLAN-TEMPLATE.md` and `PHASE-TEMPLATE.md`, (4) creates `plans/{YYMMDD}-{name}/plan.md` and all phase files, (5) presents two user checkpoints for approval, (6) self-reviews the artifacts inline.

Each phase file in frontmatter declares a `skill:` field (e.g., `postgres-expert`, `server-action-builder`) that tells the implementation session which domain skill to invoke for that phase.

**Stage 2: `/audit-plan [plan-folder]`**
Structural design audit of all phases together. Checks dependency ordering, data flow consistency, circular dependencies, and stale artifacts. Outputs a verdict (`Coherent`, `Minor Issues`, `Significant Issues`, `Major Restructuring Needed`, `Unusable`). Hard-blocks implementation if `Unusable` or `Major Restructuring Needed`.

**Stage 3: `/review-plan [plan-folder] [phase N]`**
Per-file review — one file per invocation. Two-layer check: template compliance (12 required sections) and codebase compliance (reads actual files from the project to verify code blocks match real patterns). Auto-fixes Critical/High/Medium issues directly in the phase file.

**Stage 4: `/implement [plan-folder] [group-name]`**
Solo session with full 1M context. The user opens one terminal per plan group. Each session:
1. Reads ALL phase files in the plan (cross-phase awareness)
2. Gate-checks the plan review verdict and flow audit
3. Implements each phase in its group sequentially: TDD → implement → self-verify (`pnpm test` + `pnpm run typecheck`) → self `/code-review` → commit
4. After all group phases complete: Playwright smoke check (navigate key pages, check for console errors)
5. Updates plan.md status

After all groups finish, a separate `--audit` session reviews cross-phase drift:
```bash
/implement plans/260314-auth --audit
```

### Quality Gate System

Five quality layers enforce correctness during each implementation session:

| Layer | Trigger | Checks |
|-------|---------|--------|
| **PostToolUse hook** | Every Write/Edit on `.ts`/`.tsx` | 7 regex checks: `any` types, `console.log`, missing `server-only`, hardcoded secrets, admin client misuse, default exports, missing `'use client'` |
| **TDD** | Before each phase | Write failing tests first, then implement (enforced by `task_completed.py` role-specific reminder) |
| **Self-verification** | After each phase | `pnpm test` + `pnpm run typecheck` + conditional `pnpm test:e2e` or `pnpm test:db` based on phase skill |
| **Self code-review** | After each phase | `/code-review` skill: 451-line checklist, codebase-grounded, auto-fixes Critical/High issues |
| **Playwright smoke check** | After group completes | Navigate key app pages, check console for errors, verify rendering and hydration |

Implementation is **blocked** if:
- Flow audit verdict is `Unusable` or `Major Restructuring Needed`
- Plan review verdict is `No`
- Phase contains placeholder content (`[To be detailed]`, `TBD`)
- Phase review has unresolved Critical/High issues
- Self-review fails 3+ times on the same phase (escalates to user)

### Hook Event Lifecycle

```
Session Start
    └─ session_start.py
         ├─ log_cleanup.py     (rotate JSONL if >5MB, prune sessions >30 days)
         ├─ mcp_cleanup.py     (kill orphaned MCP processes — no living Claude ancestor)
         ├─ get_git_context()  (inject branch name + dirty file count)
         └─ mcp_health.py      (warn if required MCP binaries missing)

Per Prompt
    └─ user_prompt_submit.py  (log prompt metadata, store for status display)

Per Tool Call (before)
    └─ pre_tool_use.py
         └─ check_blocked_commands()  (regex match against tiered rules)
              ├─ "deny" → block + inject reason
              └─ "ask"  → prompt user for confirmation

Per Tool Call (after — success)
    ├─ post_tool_use.py
    │    ├─ quality checks on Write/Edit TS files  (additionalContext warnings)
    │    └─ MCP output trimming  (>15,000 chars → trimmed with note)
    └─ typescript_validator.py
         └─ project-specific pattern checks  (additionalContext warnings)

Per Tool Call (after — failure)
    └─ post_tool_use_failure.py  (pattern-match error → actionable guidance)

Per Task Completion
    └─ task_completed.py
         ├─ First attempt → block with role-specific verification reminder
         └─ Subsequent attempts → allow (deduped with 5-min TTL)

Before Context Compaction
    └─ pre_compact.py  (log event, optional transcript backup)

When Claude Stops
    ├─ stop.py            (export transcript → chat.json, play completion sound)
    └─ stop_task_check.py (check for orphaned in_progress tasks, inject reminder)

Session End
    └─ session_end.py
         └─ kill_session_mcp()  (process-tree walk: kill only THIS session's MCP servers)
```

### Session Management

The framework includes sophisticated MCP server lifecycle management to prevent process accumulation:

**Problem:** MCP servers spawn deep process chains (`claude → npm → sh → node`). When Claude crashes, `SessionEnd` never fires, so leaf processes survive — reparented to init and accumulating over time. After several crashes, 100+ orphaned processes can consume gigabytes of RAM.

**Solution — Two-layer cleanup:**

1. `session_start.py` runs at startup and kills any MCP processes that have **no living Claude ancestor** in their process tree (true orphans from previous crashes)
2. `session_end.py` runs at shutdown and kills MCP processes that are **descendants of the current Claude PID** (this session's servers only)

Both layers discover MCP server patterns dynamically by reading all config files (`~/.claude.json`, `settings.json`, `settings.local.json`, `.mcp.json`) rather than using hardcoded names — so cleanup works for any project configuration.

### Security Gating

`pre_tool_use.py` intercepts every Bash tool call before execution. The blocked-commands system:

1. Loads rules from `blocked-commands.json` (tier selection + custom rules)
2. Loads the selected tier preset from `config/tiers/{tier}.json`
3. Normalizes and lowercases the command
4. Skips `git commit` and `git tag` (safe to include message text without false-positives)
5. For each rule, checks if the command matches `pattern` but NOT any `safe_patterns`
6. If matched: outputs `permissionDecision: "deny"` or `"ask"` with the reason

The `normal` tier covers 25+ rules across categories: catastrophic operations, git safety, SQL/database, file system, Docker, and miscellaneous destructive operations.

---

## Usage Guide

### Prerequisites

| Dependency | Version | Purpose |
|------------|---------|---------|
| [Node.js](https://nodejs.org/) | 18+ | Running MCP servers via npx |
| [Python](https://www.python.org/) | 3.11+ | Running hook scripts |
| [uv](https://docs.astral.sh/uv/) | Latest | Python script runner for all hooks |
| [Claude Code](https://docs.anthropic.com/en/docs/claude-code) | Latest | CLI that reads this configuration |

Optional:
- Playwright browsers (for Playwright MCP smoke checks)
- curl (for sound notifications via `notify.py`)

### Installation — Option A: Symlink (Recommended)

This approach makes skills, agents, and rules available globally. Edit files in one place — all projects benefit automatically.

```bash
# Clone the repo
git clone https://github.com/your-org/my-claude-setup.git ~/Projects/my-claude-setup

# Symlink skills and agents (directory symlinks)
ln -sf ~/Projects/my-claude-setup/.claude/skills ~/.claude/skills
ln -sf ~/Projects/my-claude-setup/.claude/agents ~/.claude/agents

# Symlink rules (per-file symlinks to avoid double-loading in this project)
mkdir -p ~/.claude/rules
for f in ~/Projects/my-claude-setup/rules/*.md; do
  ln -sf "$f" ~/.claude/rules/"$(basename "$f")"
done

# Copy hooks into each application project
cp -r ~/Projects/my-claude-setup/.claude/hooks your-project/.claude/hooks
cp ~/Projects/my-claude-setup/.claude/settings.json your-project/.claude/settings.json
cp ~/Projects/my-claude-setup/CLAUDE.md your-project/CLAUDE.md
```

> **Why per-file symlinks for rules?** If you directory-symlink `.claude/rules/` inside this repo, Claude Code loads rules twice — once from the project's `.claude/rules/` and once from `~/.claude/rules/`. Per-file symlinks from `rules/` at the repo root to `~/.claude/rules/` avoids this double-loading in this particular repo without affecting application projects.

**Add MCP servers to `~/.claude.json`:**

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "YOUR_KEY"]
    },
    "tavily": {
      "command": "npx",
      "args": ["-y", "tavily-mcp@latest"],
      "env": { "TAVILY_API_KEY": "YOUR_KEY" }
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "drawio": {
      "command": "npx",
      "args": ["-y", "@next-ai-drawio/mcp-server@latest"]
    }
  }
}
```

### Installation — Option B: Copy Per-Project

For isolated setups where global sharing is not desired:

```bash
cp -r .claude/ your-project/.claude/
cp -r rules/ your-project/.claude/rules/
cp .mcp.json.example your-project/.mcp.json
cp CLAUDE.md your-project/CLAUDE.md
# Edit .mcp.json and add your API keys
```

Updates must be applied manually to every project.

### Initial Configuration with /customize

After either installation option, run `/customize` in a Claude Code session to fill all project-specific details:

```
/customize
```

The skill collects information in four rounds:
1. **Core Identity** — project name, monorepo vs single-app, package manager, component library
2. **Architecture** — auth model, Server Action wrappers, logging approach, Supabase client paths
3. **Commands & Git** — dev/build/test commands, branch strategy, CI/CD setup
4. **Optional Features** — i18n library, test directory structure, special conventions

After collecting your answers, it fills all `<!-- CUSTOMIZE -->` markers in `CLAUDE.md` and all 16 rule files, removes template instructions, and validates completeness.

### Daily Usage Patterns

**Starting a multi-phase feature:**
```
/create-plan add voice command support to the projects list
/audit-plan plans/260318-voice-commands
/review-plan plans/260318-voice-commands
/review-plan plans/260318-voice-commands phase 1
/review-plan plans/260318-voice-commands phase 2
# ... review remaining phases

# Open multiple terminals for parallel implementation:
# Terminal 1:
/implement plans/260318-voice-commands database-layer
# Terminal 2 (once database-layer is complete or independent):
/implement plans/260318-voice-commands ui-layer

# After all groups finish:
/implement plans/260318-voice-commands --audit
```

**Quick ad-hoc changes:**
```
/dev fix the loading spinner on the projects list
/dev add a character counter to the notes textarea
/dev write unit tests for the billing service
```

**Using specialized agents:**
```
# Architecture design before building
/architect: design the schema for a notifications system

# Security audit after writing server actions
/security-reviewer: check these billing server actions for vulnerabilities

# TDD workflow for a new service
/tdd-guide: TDD the notifications service — create, list, and mark-as-read methods

# Post-implementation quality check
/code-quality-reviewer: review the code I just wrote for the notes feature
```

**Generating diagrams:**
```
/drawio-mcp create a sequence diagram for the auth flow
```

**Looking up documentation:**
```
/context7-mcp how do I use React.cache() for deduplication
/tavily-mcp latest Supabase RLS best practices 2025
```

### Running Tests

The hook test suite covers 32 tests across pre/post tool use and the TypeScript validator:

```bash
# From the my-claude-setup directory
pytest tests/hooks/

# Or using the standalone runner (no pytest installation needed)
uv run tests/hooks/run_tests.py
```

Test helpers in `conftest.py` simulate hook stdin/stdout interaction:
- `run_hook(hook_path, input_data)` — runs a hook script and returns structured output
- `make_write_input(file_path, content)` — builds a PostToolUse Write payload
- `make_edit_input(file_path, old, new)` — builds a PostToolUse Edit payload
- `make_bash_input(command)` — builds a PreToolUse Bash payload

### Troubleshooting

**Hooks not firing:**
- Verify `uv` is installed and on your PATH
- Check that `.claude/settings.json` is in the project directory (not just the user-level settings)
- Set `"disableAllHooks": false` in `settings.local.json` if hooks were previously disabled

**MCP servers not connecting:**
- Check `~/.claude.json` has the correct server definitions
- Run `which npx` to confirm Node.js is available
- For Playwright: run `npx playwright install` to install browser binaries

**Double-loading of rules:**
- If rules appear twice in Claude's context, check for both a directory symlink and individual file symlinks
- Use only per-file symlinks for rules in this repo (see installation notes)

**Hook quality checks firing on generated files:**
- Add the path to `.claude/hooks/config/quality-check-excludes.json`
- Add the path to `frontendAppPaths` in `project-checks.json` to scope framework-specific checks

**TypeScript validator firing duplicate warnings:**
- If both `post_tool_use.py` and `typescript_validator.py` warn about the same issue, one check needs to be removed from one hook
- Checks 3 (any), 6 (secrets), and 7 (admin client) were explicitly moved to `typescript_validator.py` — do not add them back to `post_tool_use.py`

---

## Notable Patterns and Design Decisions

### Solo Session Architecture (v7.0)

Prior to v7.0, the framework used ephemeral subagent teams: an orchestrator spawned builders (in isolated git worktrees), validators, and auditors as separate processes. This provided worktree isolation and 200K fresh contexts per agent.

v7.0 switched to solo sessions because **Claude Opus 4.6's 1M context window** made subagents a disadvantage: subagents only get 200K context. By running each group in its own Claude Code terminal session, every phase benefits from the full 1M window — the entire plan, all reference files, and accumulated context fit simultaneously. The user manages parallelism by opening multiple terminals.

### Codebase Grounding Over Static Checklists

Both `/review-plan` and `/code-review` read actual files from the project before flagging issues. Before warning about a pattern violation, the reviewer finds a real reference file of the same type and compares the code block against it. This prevents:
- Flagging things that are correct in this specific codebase
- Giving generic advice instead of "line X should match how it's done in file Y"

Vercel's internal evaluations showed this approach achieves near-100% accuracy vs pure checklist matching.

### Passive Context Over On-Demand Invocation

`rules/domain-patterns.md` uses `alwaysApply: true` so it loads natively into every session — including agent teammates — without any explicit skill invocation. Vercel skills research showed:
- Passive context (always loaded): 100% pattern compliance
- On-demand skill invocation: 53-79% compliance (even with explicit instructions)

The domain-patterns file compresses the most critical patterns from all 9 domain skills into ~6.8KB, with `ref:` pointers to the full skill files for when deeper guidance is needed.

### Task Descriptions as Context Compact Survival Mechanism

The `/dev` and `/implement` skills require all task descriptions to be self-contained with file paths, function signatures, and acceptance criteria. After a context compaction, `TaskGet` on the in-progress task is the only available state. A vague task description ("Create the dropdown component") leaves the agent with no recovery path; a detailed description includes enough to resume without starting over.

### Two Checkpoint Model in /create-plan

The `/create-plan` skill requires user approval at two points before self-reviewing:
1. After creating `plan.md` — verifies the feature scope and phase structure before writing individual phase files
2. After creating all phase files — verifies the phase breakdown before running reviews

Real usage showed that 20-phase plans built on wrong assumptions wasted hours of work. The two checkpoints allow course-correction at the cheapest possible points.

### Audit Before Review

`/audit-plan` runs BEFORE per-phase reviews (`/review-plan`). If a plan has structural design flaws — circular dependencies, broken execution order, incoherent data flow — reviewing individual phases is wasted effort. The audit catches fundamental brokenness first; only structurally sound plans proceed to per-phase review.

### 5–8 Medium Phases Over 30 Micro-Phases

The v7.0 phase sizing guidance shifted from the old "30 small phases > 5 large phases" rule (appropriate for 200K subagent contexts) to **5–8 coherent medium phases** per feature at 1M context. Each phase should be a complete unit of work — a service + its actions + its tests — not an individual file creation step.

### MCP Output Trimming

`post_tool_use.py` trims MCP tool outputs that exceed 15,000 characters and appends a note explaining the trim and suggesting more targeted queries. This prevents large MCP outputs (e.g., documentation fetches, browser page dumps) from flooding the context window and degrading response quality.

### Separation of Concerns Between Hooks

The two PostToolUse hooks (`post_tool_use.py` and `typescript_validator.py`) have explicitly documented ownership to prevent duplicate warnings. Each check lives in exactly one hook:
- Generic/framework-agnostic checks → `post_tool_use.py`
- TypeScript-specific checks + project-specific config-driven checks → `typescript_validator.py`

This separation is documented with comments in both files and in the README.

---

## Future Enhancements

The following improvements have been identified but deferred (see `/docs/future-enhancements.md`):

| Enhancement | Description | Effort |
|-------------|-------------|--------|
| `/amend-plan` skill | Incremental re-planning — add, split, remove, and reorder phases mid-implementation | Half day |
| `/pipeline-stats` skill | Pipeline health metrics — per-skill failure rates, common audit findings | 2–3 hours |
| Rule/Skill deconfliction audit | Audit overlapping rule/skill pairs (`forms.md` vs `react-form-builder`, etc.) for contradictions | 2–3 hours |
| PostToolUse hook merge | Merge `post_tool_use.py` and `typescript_validator.py` into a single hook to reduce redundant I/O | 1–2 hours (after test suite complete) |
| MCP wrapper skill consolidation | Evaluate whether 5 MCP wrapper skills duplicate `mcp-tools.md` rule content; remove if so | 1 hour |
| Sequential Thinking evaluation | Check `hooks.jsonl` for actual usage frequency; remove if rarely invoked | 15 minutes |

---

*This documentation was generated from a complete recursive analysis of the `my-claude-setup` repository on 2026-03-21.*
