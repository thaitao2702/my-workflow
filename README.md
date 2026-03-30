# AI Coding Workflow

A Claude Code framework that transforms AI-assisted development from ad-hoc prompting into a structured, repeatable engineering process.

## At a Glance

This workflow has **two core pillars**:

**1. Living Knowledge Layer** — The system builds and maintains persistent understanding of your codebase at two tiers: a project overview (architecture, flows, data model) and per-component analysis docs (APIs, hidden behaviors, edge cases, lessons learned). Every execution enriches this knowledge — wrong assumptions, integration gotchas, and failure modes are permanently captured so the same mistakes never repeat.

**2. Pattern Reuse** — When the same type of work happens repeatedly in a project (new API endpoint, new provider integration, new CRUD page), the system extracts the pattern into a reusable template. Templates capture not just the code structure, but the steps, decisions, gotchas, and what varies vs what stays fixed. Next time, instead of planning from scratch, the template accelerates the entire plan-execute cycle.

**8 commands, 6 specialized agents, orchestrated by the main agent:**

| Command | Purpose |
|---------|---------|
| `/initialize` | Scan project, create overview (run once) |
| `/plan` | Turn requirements into phased execution plan |
| `/execute` | Implement plan with TDD, review, state tracking |
| `/analyze` | Deep-analyze a component, produce analysis doc |
| `/doc-update` | Update docs from code changes + executor discoveries |
| `/template-create` | Extract repeatable pattern from completed work |
| `/template-apply` | Use a template to accelerate new implementation |
| `/jira` | Fetch Jira ticket as clean markdown |

**The feedback loop:**

```
  /execute discovers hidden behaviors, edge cases
       │
       ▼
  /doc-update captures them in .analysis.md
       │
       ▼
  /plan reads enriched analysis docs ──► better plans ──► fewer surprises
       │
       ▼
  /template-create extracts proven patterns
       │
       ▼
  /template-apply accelerates the next similar feature
```

## Table of Contents

- [Quick Start](#quick-start)
- [What Problem Does This Solve](#what-problem-does-this-solve)
- [Core Concepts](#core-concepts)
  - [Pillar 1: The Knowledge Layer](#pillar-1-the-knowledge-layer)
  - [Pillar 2: Pattern Reuse](#pillar-2-pattern-reuse)
- [Workflow Overview](#workflow-overview)
- [Skills Reference](#skills-reference)
  - [/initialize](#initialize--initialize-project)
  - [/plan](#plan--create-execution-plan)
  - [/execute](#execute--execute-plan)
  - [/analyze](#analyze--deep-component-analysis)
  - [/doc-update](#doc-update--update-documentation)
  - [/template-create](#template-create--extract-pattern)
  - [/template-apply](#template-apply--use-template)
  - [/jira](#jira--fetch-jira-ticket)
- [Architecture](#architecture)
- [Quality System](#quality-system)
- [State Management & Resume](#state-management--resume)
- [Configuration](#configuration)
- [Directory Structure](#directory-structure)

## Quick Start

1. Copy `.claude/` and `.workflow/` directories + `CLAUDE.md` into your project root
2. Edit `.workflow/config.json` — set `project_name` and project-specific settings
3. Run `/initialize` to scan your project and generate an overview
4. Plan work: `/plan "Add user export feature"`
5. Execute: `/execute`

## What Problem Does This Solve

Without structure, AI coding sessions are stateless — every conversation starts from zero. The agent rediscovers the same architecture, re-reads the same files, makes the same wrong assumptions, and produces inconsistent results. Knowledge is lost between sessions.

This workflow solves that by providing:

| Problem | Solution |
|---------|----------|
| Agent doesn't understand the codebase | `/initialize` creates a project overview loaded every session |
| Agent misunderstands component behavior | `/analyze` produces deep component docs with hidden behaviors, edge cases |
| Plans are unrealistic or miss constraints | `/plan` reads analysis docs + source code before designing tasks |
| Implementation is ad-hoc, untested | `/execute` enforces TDD, code review, and state tracking per phase |
| Knowledge is lost after each session | `/doc-update` captures discoveries back into analysis docs |
| Same mistakes repeat across features | Wrong assumptions and edge cases are recorded permanently |
| Similar features are built from scratch each time | `/template-create` and `/template-apply` capture and reuse patterns |
| Work is lost when sessions interrupt | Resumable state tracking — pick up exactly where you left off |

## Core Concepts

### Pillar 1: The Knowledge Layer

The heart of this workflow is a **two-tier knowledge layer** that persists across sessions and grows richer with every feature implemented.

```
Tier 1: Project Level                    Tier 2: Component Level
┌─────────────────────────┐              ┌────────────────────────────────┐
│ project-overview.md     │              │ {Component}.analysis.md        │
│                         │              │                                │
│ - What the project does │              │ - Purpose & public API         │
│ - Tech stack            │              │ - Integration patterns         │
│ - System architecture   │              │ - Hidden behaviors             │
│ - Module responsibilities│             │ - Edge cases & failure modes   │
│ - Core user flows       │              │ - Dependencies & interactions  │
│ - Data model & ER       │              │ - Invariants & constraints     │
│ - External integrations │              │ - Accumulated experience:      │
│ - Conventions           │              │   wrong assumptions caught,    │
│                         │              │   gotchas from real impl,      │
│ Created by: /initialize │              │   lessons learned              │
│ Updated by: /execute    │              │                                │
└─────────────────────────┘              │ Created by: /analyze           │
                                         │ Updated by: /doc-update        │
                                         │ Enriched by: executor findings │
                                         └────────────────────────────────┘
```

**How the knowledge layer is used:**

- **`/plan`** reads analysis docs first (hash-verified fresh), falls back to source code only when docs are stale or missing. This saves significant tokens and gives the planner accumulated experience that raw source code doesn't contain.
- **`/execute`** ensures analysis docs are fresh before each phase (analysis gate). The executor receives component docs alongside source code.
- **`/doc-update`** patches analysis docs after execution — both from code changes (git diff) and from executor discoveries (hidden behaviors, wrong assumptions).
- **Every execution makes the knowledge richer.** Failed assumptions, edge cases, and hidden behaviors discovered during implementation are permanently recorded. The next plan that touches the same component benefits from all prior experience.

**Staleness detection:** Analysis docs include a `source_hash` (SHA-256 of source files) and `dependency_tree` hashes in their frontmatter. Any skill can verify freshness in milliseconds by comparing hashes — no git dependency, catches uncommitted changes.

### Pillar 2: Pattern Reuse

Most projects have repeatable integration patterns — adding a new API endpoint, connecting a new payment provider, creating a new CRUD page, adding a new event handler. Each instance follows the same structural shape with different specifics. Without templates, every instance is planned and implemented from scratch, rediscovering the same steps, the same integration points, and the same gotchas.

The template system captures these patterns after they've been **proven through execution**:

```
First time: /plan ──► /execute ──► works! ──► /template-create
                                                    │
                                            Extracts the pattern:
                                            - Steps (what to do)
                                            - Variables (what changes)
                                            - Fixed parts (what stays the same)
                                            - Gotchas (what to watch out for)
                                            - Reference files (annotated code)
                                                    │
                                                    ▼
Next time:  /template-apply ──► /plan (enriched) ──► /execute
            Fills variables,        Adapts to current
            answers guided          codebase state,
            sections                quality review
```

**Variability markers** classify each part of the pattern:

| Marker | Meaning | Example |
|--------|---------|---------|
| `[F]` Fixed | Copy as-is every time | Error handling wrapper, config registration, middleware setup |
| `[P]` Parametric | Same structure, swap values | API paths, column names, component names, route definitions |
| `[G]` Guided | Follow the shape, expect differences | Vendor-specific UI, custom validation, business-specific logic |

**Multi-case reasoning:** The template extractor doesn't just record what happened — it imagines 2-3 variant scenarios (e.g., "what if this were PayPal instead of Stripe?") to discover what's truly fixed vs parametric vs guided. What survives across all imagined variants is the real pattern.

**Templates always go through `/plan`** — because the codebase may have changed since the template was created, and guided sections need adaptation. Templates accelerate planning; they don't bypass it.

**Real examples of when templates help:**
- Adding a new payment provider (Stripe done, now PayPal, now Crypto)
- Creating a new API resource (users done, now orders, now products)
- Adding a new game to a game platform (same lifecycle, different mechanics)
- Integrating a new third-party service (same auth pattern, different API)
- Creating a new admin CRUD page (same table/form/detail structure, different entity)

## Workflow Overview

```
                         ┌─────────────────────────────────────────────┐
                         │         KNOWLEDGE LAYER (persistent)        │
                         │                                             │
                         │  project-overview.md    *.analysis.md       │
                         │  (project level)        (component level)   │
                         └──────┬──────────────────────┬───────────────┘
                                │                      │
         ┌──────────────────────┼──────────────────────┼────────────────┐
         │                      ▼                      ▼                │
         │  /initialize ──► creates overview    /analyze ──► creates    │
         │                                              component docs  │
         │                      │                      │                │
         │                      ▼                      ▼                │
         │  /plan ◄──── reads overview + analysis docs (hash-verified)  │
         │    │         falls back to source if stale/missing           │
         │    │                                                         │
         │    ├── /template-apply (if matching template found)          │
         │    │                                                         │
         │    ▼                                                         │
         │  /execute ──► analysis gate (ensures fresh docs)             │
         │    │          executor (TDD per phase)                       │
         │    │          reviewer (per phase)                           │
         │    │                                                         │
         │    ├── executor discovers hidden behaviors, edge cases ──┐   │
         │    │                                                     │   │
         │    ▼                                                     ▼   │
         │  /doc-update ◄── git diff + plan context + discoveries      │
         │    │              updates analysis docs + overview           │
         │    │                                                         │
         │    ▼                                                         │
         │  /template-create (if repeatable pattern detected)           │
         │    │                                                         │
         │    ▼                                                         │
         │  .workflow/templates/{name}/ (reusable for next time)        │
         └──────────────────────────────────────────────────────────────┘
```

**The feedback loop:** `/execute` produces discoveries --> `/doc-update` writes them into analysis docs --> next `/plan` reads enriched docs --> better plans --> fewer surprises during execution.

## Skills Reference

### `/initialize` -- Initialize Project

Performs a shallow, wide scan of the entire project to generate a concise overview that every agent reads at the start of every session.

**Usage:**
```
/initialize
```

**When to use:**
- First time setting up the workflow on a project
- After major structural changes (new modules, framework migration, architecture shift)

**Flow:**

```
/initialize
    │
    ├── 1. Discovery (language-agnostic)
    │   ├── Detect project type (manifest files)
    │   ├── Scan project structure
    │   ├── Read existing docs (README, ADRs)
    │   ├── Read config files (build, lint, CI/CD)
    │   ├── Read entry points
    │   ├── Read routing / API surface
    │   ├── Read database schema
    │   └── Identify 3-5 core user flows
    │
    ├── 2. Analysis
    │   └── Synthesize: stack, architecture, modules,
    │       flows, data model, integrations, conventions
    │
    ├── 3. Write project-overview.md
    │   └── Max ~4k tokens, mandatory Mermaid diagrams
    │       (system context, architecture, data flow, ER)
    │
    └── 4. User review
        └── User corrects any inaccuracies
```

**Output:** `.workflow/project-overview.md` — loaded into every session via `CLAUDE.md`. Contains: what the project does, tech stack, system architecture diagram, project structure, modules table, core user flows, data model with ER diagram, external integrations, patterns/conventions, testing setup, build/deploy pipeline.

---

### `/plan` -- Create Execution Plan

Transforms requirements into a phased, dependency-aware execution plan. The planner reads the knowledge layer first to understand constraints before designing tasks.

**Usage:**
```
/plan "Add user export feature"
/plan ./requirements/export.md
/plan gh:123
/plan jira:PROJ-456
```

**When to use:**
- Starting any non-trivial feature, refactor, or bug fix
- When you want structured, reviewable, resumable execution

**Flow:**

```
/plan "requirements"
    │
    ├── A. Requirement Gathering
    │   ├── Parse input (text, file, GitHub issue, Jira)
    │   ├── Check template index for keyword matches
    │   │   └── If match: /template-apply ──► enriched input
    │   ├── Read project-overview.md
    │   ├── Note which components have .analysis.md
    │   └── Clarify ambiguities with user (max 3 rounds)
    │
    ├── B. Component Intelligence (analysis-first)
    │   ├── For each affected component:
    │   │   ├── .analysis.md exists?
    │   │   │   ├── YES ──► hash source + dependencies
    │   │   │   │   ├── All match (fresh) ──► read analysis doc
    │   │   │   │   │   └── Enough info? ──► skip source
    │   │   │   │   │       └── Need more? ──► read source selectively
    │   │   │   │   └── Mismatch (stale) ──► read source directly
    │   │   │   └── NO ──► read source directly
    │   │   └── Capture: constraints, hidden behaviors, patterns
    │   └── DO NOT invoke /analyze (deferred to execution)
    │
    ├── C. Plan Creation (main agent, not subagent)
    │   ├── Design phased plan with dependency graph
    │   ├── User direction checkpoint (approve before writing files)
    │   └── Write plan.json + phase-{N}.json files
    │
    ├── D. Quality Review
    │   └── Reviewer subagent checks quality dimensions
    │       (max 2 revision rounds, then escalate to user)
    │
    ├── E. User Approval & Finalization
    │   ├── User review: approve / request changes / reject
    │   └── Initialize state.json via CLI
    │
    └── F. Post-Planning Reflection
        └── Surface non-trivial discoveries about
            architecture, components, or project overview
            that should be documented
```

**Key design choices:**
- Planning runs in the **main agent** (not a subagent) — it needs user interaction and full context
- Analysis docs are the **primary source** when hash-verified fresh — they contain accumulated experience that source code alone doesn't have
- Tasks describe **WHAT and WHY**, never HOW — the executor decides implementation by reading source
- Acceptance criteria must be **verifiable by running something** (a test, a command, a query)

**Output:** `.workflow/plans/{YYMMDD}-{name}/` with `plan.json`, `phase-{N}.json`, `state.json`

---

### `/execute` -- Execute Plan

Implements the approved plan phase-by-phase with TDD, code review, state tracking, and a final reconciliation pass that feeds discoveries back into the knowledge layer.

**Usage:**
```
/execute                    # latest approved plan
/execute {plan-path}        # specific plan
/execute --resume           # continue interrupted work
```

**When to use:**
- After `/plan` produces an approved plan
- To resume interrupted work from a previous session

**Flow:**

```
/execute
    │
    ├── 1. Load Plan
    │   ├── Resolve $PLAN_DIR
    │   ├── Read plan.json + all phases
    │   └── If resuming: get resume point from CLI
    │
    ├── 2. Execute Groups (sequential: A → B → C)
    │   │
    │   └── For each phase in group:
    │       │
    │       ├── 2a. Analysis Gate
    │       │   └── For each affected component:
    │       │       ├── .analysis.md exists + fresh? ──► read it
    │       │       ├── .analysis.md stale? ──► /analyze --recursive
    │       │       └── Missing? ──► /analyze --recursive
    │       │
    │       ├── 2b. Executor Subagent (one per phase)
    │       │   ├── Receives: mission briefing, component intelligence,
    │       │   │   risks, phase goal, tasks, analysis docs, rules
    │       │   ├── Implements all tasks sequentially with TDD
    │       │   ├── Tracks task completion via CLI
    │       │   └── Reports ## Discoveries at end
    │       │
    │       ├── 2c. Reviewer Subagent
    │       │   └── Reviews code quality (max 2 fix rounds)
    │       │
    │       ├── 2d. Playwright Check (if UI components)
    │       │
    │       └── 2e. Phase Completion + regression tests
    │
    └── 3. Final Reconciliation
        │
        ├── 3a. Reconciliation Pass
        │   ├── Gather cumulative git diff + discoveries
        │   ├── Classify discoveries:
        │   │   ├── Component-level ──► passed to /doc-update
        │   │   └── Project-level ──► handled by orchestrator
        │   ├── For each affected component:
        │   │   └── /doc-update (diff + plan context + discoveries)
        │   └── Project-level updates:
        │       ├── project-overview.md (if architecture changed)
        │       ├── .workflow/rules/planning/ (wrong assumptions)
        │       └── .workflow/rules/code/ (pattern corrections)
        │
        ├── 3b. Template Suggestion
        │   └── If repeatable pattern: suggest /template-create
        │
        └── 3c. Final Verification
            ├── Full test suite
            └── Mark execution complete
```

**Key design choices:**
- **One executor subagent per phase** (not per task) — saves ~12,000 tokens on a 4-task phase and the executor builds on its own work naturally
- **Analysis gate ensures fresh docs** before each phase — the executor gets reliable component knowledge
- **Executor reports discoveries** — hidden behaviors, wrong assumptions, edge cases found during implementation
- **Doc-update receives discoveries** — component-level findings are written into analysis docs automatically; project-level findings are presented to the user
- **Documentation updates happen once** at the end, not per-phase — avoids redundant updates when multiple phases touch the same component

**Resume:** Sessions can interrupt at any point. The CLI tracks phase/task/substep progress. Run `/execute --resume` to continue from the exact point where work stopped.

---

### `/analyze` -- Deep Component Analysis

Performs deep, recursive analysis of a component and produces co-located documentation. This is the primary mechanism for building the component-level knowledge layer.

**Usage:**
```
/analyze src/services/authService.ts
/analyze src/modules/auth --recursive
```

**When to use:**
- Before working on a complex component for the first time
- When the execute analysis gate detects missing or stale docs
- After major refactors (doc-update will trigger this for MAJOR changes)

**Flow:**

```
/analyze src/services/authService.ts
    │
    ├── 1. Parse input & resolve path
    │
    ├── 2. Staleness check
    │   ├── .analysis.md exists?
    │   │   ├── Hash source files, compare with source_hash
    │   │   ├── Hash dependencies, compare with dependency_tree
    │   │   ├── All match ──► "Already current, skipping"
    │   │   └── Mismatch ──► proceed (update mode)
    │   └── Missing ──► proceed (full mode)
    │
    ├── 3. Dependency resolution (if --recursive)
    │   ├── Parse imports, resolve aliases (@/, ~/)
    │   ├── Build dependency tree
    │   └── Topological sort (analyze leaves first)
    │
    ├── 4. Size guard (warn if >8000 lines)
    │
    ├── 5. Analyzer subagent
    │   ├── Receives: source code + dependency graph
    │   ├── Analyzes bottom-up in one session
    │   └── Produces .analysis.md with:
    │       ├── Frontmatter (hash, timestamps, dependencies)
    │       ├── CONTENT: Purpose, Dependencies, Public API,
    │       │   Integration Patterns, Architecture, Entrypoints,
    │       │   Patterns, Hidden Details
    │       └── EXTRA: Tests, Performance Notes
    │
    └── 6. Verify output artifact exists
```

**Output:** `{ComponentName}.analysis.md` co-located with the source file.

**Progressive loading levels:**
| Level | Contents | Tokens | Use case |
|-------|----------|--------|----------|
| Level 0 | Frontmatter only | ~50 | Scanning, staleness checks |
| Level 1 | + CONTENT section | ~300-500 | Planning, understanding API |
| Level 2 | Full document | ~500-800 | Modifying the component |

**Modes:**
| Mode | Trigger | Model | Scope |
|------|---------|-------|-------|
| Full | First analysis | Opus | Complete from scratch |
| Update | Source hash changed | Sonnet | Incremental — changed sections only |
| Recursive | `--recursive` flag | Opus/Sonnet | Component + all dependencies (leaf-first) |

---

### `/doc-update` -- Update Documentation

Assesses whether code changes warrant documentation updates and applies the right level of update. Receives executor discoveries to capture experiential knowledge alongside code changes.

**Usage:**
```
/doc-update
```

Usually called automatically by `/execute` during final reconciliation. Can also be run manually.

**When to use:**
- Automatically after `/execute` completes (per affected component)
- Manually after making changes outside the workflow

**Flow:**

```
/doc-update {component}
    │
    ├── 0. Check .analysis.md exists
    │   ├── Missing (new component) ──► /analyze (full) ──► done
    │   └── Exists ──► proceed
    │
    ├── 1. Doc-updater subagent
    │   ├── Receives: git diff, existing analysis, project overview,
    │   │   plan context, executor discoveries for this component
    │   ├── Classifies: NO UPDATE / MINOR / MAJOR
    │   └── Acts:
    │       ├── NO UPDATE (no discoveries) ──► report only
    │       ├── NO UPDATE (with discoveries) ──► escalate to MINOR
    │       │   (experiential knowledge must be recorded even if
    │       │    code change was trivial)
    │       ├── MINOR ──► patches .analysis.md inline
    │       │   (add table rows, update hash, add discoveries
    │       │    to Hidden Details)
    │       └── MAJOR ──► reports, recommends /analyze
    │
    ├── 2. Orchestrator handles result
    │   ├── NO UPDATE ──► next component
    │   ├── MINOR ──► proceed to verify
    │   └── MAJOR ──► invoke /analyze
    │
    └── 3. Verify
        ├── .analysis.md exists
        ├── source_hash matches current file
        └── Required fields populated
```

**The discovery capture flow:** When the executor finds something unexpected during implementation — a hidden retry mechanism, an API that doesn't match its docs, an edge case the plan didn't anticipate — that finding is passed to `/doc-update` as a component-level discovery. The doc-updater writes it into the Hidden Details table of the component's `.analysis.md`. This means the next `/plan` that reads this component's analysis doc will see the finding and plan accordingly.

---

### `/template-create` -- Extract Pattern

Extracts a repeatable implementation pattern from completed work into a reusable template. Best invoked immediately after `/execute` completes, while the full execution context is still fresh.

**Usage:**
```
/template-create payment-provider
/template-create                     # interactive source selection
```

**When to use:**
- After `/execute` completes work that will likely be repeated with variations
- Suggested automatically by `/execute` Step 3b if a repeatable pattern is detected

**Flow:**

```
/template-create {name}
    │
    ├── 0. Determine source mode
    │   ├── [1] Current session (richest — from just-completed /execute)
    │   ├── [2] Completed plan on disk
    │   ├── [3] Git branch or commit range
    │   ├── [4] Specific files or component
    │   └── [5] Manual description
    │
    ├── 1. Gather source material
    │   ├── Git diff, plan summary, phase/task structure
    │   ├── Component intelligence, execution discoveries
    │   ├── Key decisions and trade-offs
    │   └── .analysis.md files for touched components
    │
    ├── 2. Template-extractor subagent
    │   ├── Multi-case reasoning: imagines 2-3 variant scenarios
    │   ├── Classifies each step as:
    │   │   ├── [F] Fixed — copy as-is every time
    │   │   ├── [P] Parametric — same structure, swap values
    │   │   └── [G] Guided — follow the shape, expect differences
    │   └── Produces complete template + annotated reference files
    │
    ├── 3. User validates summary (direction check)
    │
    ├── 4. User validates full template (detail check)
    │
    └── 5. Save to .workflow/templates/{name}/
        ├── template.md (overview, steps, variables, gotchas)
        ├── references/ (annotated source snapshots)
        └── Update index.md
```

**Source options (richest to leanest):**
| Source | Available context | Quality |
|--------|------------------|---------|
| Current session (post-execute) | Plan reasoning, decisions, discoveries, diff, analysis docs | Best |
| Completed plan on disk | Plan intent, task structure, diff, analysis docs | Good |
| Git history | Commit messages, diff | Moderate |
| Existing code | Current file state | Basic |
| Manual description | User's words | Minimal |

---

### `/template-apply` -- Use Template

Applies an existing template to accelerate a new implementation. Always produces input for `/plan` — templates are patterns, not plans.

**Usage:**
```
/template-apply payment-provider
```

**When to use:**
- When building something similar to a previous implementation
- Auto-suggested by `/plan` when template keywords match requirements

**Flow:**

```
/template-apply {name}
    │
    ├── 1. Load template
    │   ├── Read template.md + references/
    │   └── Present overview to user
    │
    ├── 2. Collect variables
    │   ├── For each [P] variable: ask user for value
    │   └── For each [G] section: ask how it differs
    │
    └── 3. Generate plan input
        ├── Transform steps into structured requirements
        │   ├── [F] ──► concrete requirements with exact instructions
        │   ├── [P] ──► requirements with variable values substituted
        │   └── [G] ──► requirements with user-provided details
        ├── Include: reference files, gotchas, guided answers
        └── Hand off to /plan
            ├── If invoked by /plan: return as enriched input
            └── If invoked directly: invoke /plan with the document
```

**Key design choice:** Templates always go through `/plan` for quality review and adaptation to current codebase state. There is no "skip to execute" shortcut — templates need planning because the codebase may have changed since the template was created.

---

### `/jira` -- Fetch Jira Ticket

Fetches a Jira ticket and transforms its ADF (Atlassian Document Format) content into clean markdown suitable for `/plan` input.

**Usage:**
```
/jira PROJ-456
```

**When to use:**
- When requirements live in Jira and you want to plan from them

Requires `jira_fetch.py` setup and `JIRA_TOKEN` environment variable. Configure in `.workflow/config.json`.

## Architecture

### Orchestrator + Subagent Design

```
┌─────────────────────────────────────────────────────────────┐
│                    MAIN AGENT (Orchestrator)                 │
│                                                             │
│  Skills define WHAT, WHERE, WHEN:                           │
│  - Parse input, determine steps                             │
│  - Collect context for subagents                            │
│  - Fill prompt templates with collected data                │
│  - Verify output artifacts                                  │
│  - Cross-call other skills                                  │
│  - User interaction (checkpoints, approvals)                │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐  │
│  │ executor │  │ analyzer │  │ reviewer │  │doc-updater│  │
│  │          │  │          │  │          │  │           │  │
│  │ HOW to   │  │ HOW to   │  │ HOW to   │  │ HOW to    │  │
│  │implement │  │ analyze  │  │ review   │  │ assess &  │  │
│  │ with TDD │  │ code     │  │ quality  │  │ patch docs│  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────┘  │
│  ┌────────────────┐  ┌────────────────┐                    │
│  │template-extract│  │template-applier│                    │
│  │                │  │                │                    │
│  │ HOW to find    │  │ HOW to         │                    │
│  │ the pattern    │  │ substitute     │                    │
│  └────────────────┘  └────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

**Skills own WHAT/WHERE/WHEN.** They define the workflow: parse input, determine which steps to run, what context to give the agent, what format the output should be, how to verify results. Skills run in the main session — they can cross-call other skills and spawn agents.

**Agents own HOW to think.** They bring domain expertise: how to read code, how to assess significance, how to decompose requirements, when to escalate vs decide. Agents run as subagents in isolated context windows.

**Prompt templates** bridge the two layers. Each skill has a `-prompt.md` file that defines: what data the orchestrator must collect (and where to find it), and what prompt the subagent receives (with placeholders for that data). The orchestrator fills the template; the agent executes it.

### Agents

| Agent | Model | Role |
|-------|-------|------|
| **executor** | Sonnet | Implements tasks with TDD, reports discoveries |
| **analyzer** | Opus | Deep component analysis, bottom-up recursive |
| **reviewer** | Sonnet | Quality gate for plans and code |
| **doc-updater** | Sonnet | Change significance assessment, surgical doc patches |
| **template-extractor** | Opus | Pattern abstraction via multi-case reasoning |
| **template-applier** | Sonnet | Variable substitution + plan input generation |

**Cost optimization:** Opus for tasks requiring synthesis and judgment (analysis, pattern extraction). Sonnet for mechanical or checklist-based tasks (execution, review, doc updates). Configurable per-agent in `.workflow/config.json`.

**Planning runs in the main agent** — it needs user interaction (clarification, direction approval, final review) and accumulates context across phases. No planner subagent.

## Quality System

### Three Layers

**Layer 1: General rules** (`.claude/rules/`, always loaded)
- `quality-criteria.md` — Type safety, error handling, security, testing, code hygiene
- `tdd-policy.md` — Pragmatic TDD: tests first by default, documented exceptions for UI, config, types
- `security-gates.md` — Blocked commands (DROP DATABASE, force push to main, rm -rf /) + confirmation gates for risky operations
- `resume-protocol.md` — How to detect and resume interrupted executions

**Layer 2: Project-specific rules** (`.workflow/rules/`)
- `planning/` — Rules for plan review (loaded by reviewer during planning)
- `code/` — Rules for code review (loaded by reviewer during execution)

Add rules by dropping `.md` files:
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

**Layer 3: Plan-specific criteria** — Acceptance criteria per task, verified during phase review.

## State Management & Resume

All plan/phase/state data is stored as JSON. All reads and writes go through `workflow_cli.py` — no manual file editing.

```bash
# Read
python .claude/scripts/workflow_cli.py state current --plan-dir $PLAN_DIR
python .claude/scripts/workflow_cli.py phase tasks 2 --plan-dir $PLAN_DIR
python .claude/scripts/workflow_cli.py plan show --plan-dir $PLAN_DIR

# Write
python .claude/scripts/workflow_cli.py state complete-task 1 task-01 --plan-dir $PLAN_DIR
python .claude/scripts/workflow_cli.py state start-phase 2 --plan-dir $PLAN_DIR
python .claude/scripts/workflow_cli.py state log "Phase 1 completed" --plan-dir $PLAN_DIR
```

**Why JSON + CLI instead of markdown:**
- Token efficient — read one field (~20 tokens) instead of full file (~300+ tokens)
- Reliable — atomic structured writes, no string-matching edits
- Parallel-safe — CLI does read-modify-write atomically
- No format drift — structured data stays structured

**Status lifecycles:**
- **Plan:** `draft` -> `reviewed` -> `approved` -> `executing` -> `completed`
- **Phase:** `pending` -> `in_progress` -> `completed`
- **Task:** `pending` -> `active` -> `completed` | `failed` | `skipped`

**Resume:** When a session is interrupted (context limit, user stops, crash), the CLI preserves exact progress. Next session: `/execute --resume` picks up from the exact phase/task/substep.

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

## Directory Structure

```
.claude/
├── skills/                      # Workflow commands (8 skills)
│   ├── initialize/SKILL.md      #   Project overview scan
│   ├── plan/SKILL.md            #   Execution plan creation
│   ├── execute/SKILL.md         #   Plan execution
│   │   ├── executor-prompt.md   #     Prompt template for executor
│   │   └── reviewer-prompt.md   #     Prompt template for reviewer
│   ├── analyze/SKILL.md         #   Deep component analysis
│   │   └── analyzer-prompt.md   #     Prompt template for analyzer
│   ├── doc-update/SKILL.md      #   Documentation updates
│   │   └── doc-updater-prompt.md#     Prompt template for doc-updater
│   ├── template-create/SKILL.md #   Pattern extraction
│   │   └── template-extractor-prompt.md
│   ├── template-apply/SKILL.md  #   Pattern application
│   └── jira/SKILL.md            #   Jira ticket fetching
├── agents/                      # Specialized subagents (6 agents)
│   ├── executor.md              #   TDD implementation specialist
│   ├── analyzer.md              #   Code analysis specialist
│   ├── reviewer.md              #   Quality review specialist
│   ├── doc-updater.md           #   Documentation maintenance specialist
│   ├── template-extractor.md    #   Pattern abstraction specialist
│   └── template-applier.md      #   Template application specialist
├── scripts/
│   ├── workflow_cli.py          #   Plan/phase/state JSON CLI
│   └── workflow_cli.reference.md#   CLI command reference
├── rules/                       # Always-loaded quality rules
│   ├── quality-criteria.md
│   ├── tdd-policy.md
│   ├── security-gates.md
│   └── resume-protocol.md
└── settings.json                # Claude Code settings

.workflow/
├── config.json                  # Project configuration
├── project-overview.md          # Generated by /initialize (Tier 1 knowledge)
├── rules/                       # Project-specific quality rules
│   ├── planning/                #   Rules loaded during plan review
│   └── code/                    #   Rules loaded during code review
├── templates/                   # Reusable patterns
│   ├── index.md                 #   Template discovery index
│   └── {name}/
│       ├── template.md          #   Template definition
│       └── references/          #   Annotated source snapshots
└── plans/                       # Execution history
    └── {YYMMDD}-{name}/
        ├── plan.json            #   Plan definition
        ├── phase-{N}.json       #   Phase definitions
        └── state.json           #   Execution state (CLI-managed)

Component docs (Tier 2 knowledge, co-located with source):
  src/services/authService.analysis.md
  src/components/Dashboard.analysis.md
  src/modules/auth/auth.analysis.md
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Knowledge layer as core | AI agents make better decisions with accumulated experience. Analysis docs grow richer with every execution — hidden behaviors, wrong assumptions, edge cases are permanently captured. |
| Analysis-first planning | Plan reads hash-verified analysis docs before source code. Fresh docs contain accumulated experience that raw source doesn't. Falls back to source only when stale/missing. |
| Skill + Agent two-layer | Skills define workflow (WHAT/WHEN), agents bring expertise (HOW). Clear separation. No intermediate "procedures" layer needed. |
| Prompt templates | Bridge skills and agents. Orchestrator collects data, fills template, spawns agent. Agent never needs to search for its own context. |
| JSON + CLI for state | Token efficient, atomic writes, parallel-safe, no format drift. Read one field (~20 tokens) vs full markdown file (~300+ tokens). |
| Doc updates at end, not per-phase | Avoids redundant updates when multiple phases touch same component. One assessment per component with full cumulative diff. |
| Discoveries flow into doc-update | Executor findings (hidden behaviors, wrong assumptions) are passed to doc-update alongside the git diff. Component-level findings go into analysis docs; project-level findings are handled by the orchestrator. |
| Templates always go through /plan | Templates are patterns, not plans. They need adaptation to current codebase state and quality review. No "skip to execute" shortcut. |
| Template suggestion after execute, not plan | A plan is unproven theory. Only suggest template extraction after execution validates the pattern works. |
| Component docs co-located with source | Path IS the namespace. Same pattern as `.test.tsx`. Moves with the file. Git-friendly. |
| Opus for synthesis, Sonnet for execution | Analysis and pattern extraction need deep reasoning (Opus). Implementation and review are checklist-based (Sonnet at lower cost). |
| Pragmatic TDD | Tests first by default. Documented exceptions for UI, config, types. Not dogmatic — exceptions are per-task, not per-project. |
| One executor per phase, not per task | Saves ~12k tokens on a 4-task phase. Executor builds on its own work naturally within a phase. |
