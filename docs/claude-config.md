# claude-config: AI Workflow Framework Documentation

**Source repository:** `E:/Project/My Workflow/claude-config`
**Author:** solatis (https://github.com/solatis/claude-config)

---

## Overview / Purpose

`claude-config` is a structured AI workflow framework designed to be installed as the Claude Code configuration directory (`.claude`). Its core insight is that LLM-assisted coding fails over the long term because LLMs accumulate technical debt invisibly, context windows degrade with size rather than improve, and models will confidently implement the wrong thing without surfacing ambiguity.

The framework addresses this with four engineering principles:

1. **Context Hygiene** -- Each task receives exactly the information it needs, no more. Just-in-time loading via a two-file documentation hierarchy (`CLAUDE.md` as navigation index, `README.md` as invisible knowledge store).
2. **Planning Before Execution** -- Structured planning phases force ambiguities to surface before code is written. Plans are written to files so reasoning survives context resets.
3. **Review Cycles** -- Execution is split into milestones with quality gates at each stage. A technical writer checks clarity; a quality reviewer checks completeness. No milestone advances without passing review.
4. **Cost-Effective Delegation** -- An orchestrator delegates to smaller, cheaper models (Haiku for simple tasks, Sonnet for moderate complexity), escalating to more powerful models only for genuine ambiguity.

The intended user is an engineer who uses Claude Code daily and wants structured, maintainable results rather than fast-but-rotting code.

---

## Key Features

- **Planner skill** with a 14-step planning workflow and a 9-step execution workflow, both with quality gates and automatic retry loops
- **DeepThink skill** for structured multi-step reasoning on open-ended analytical questions, with auto-detected quick/full modes
- **Refactor skill** that analyzes code across 10 parallel dimensions (naming, extraction, types, modules, architecture, etc.) and produces prioritized work items
- **Codebase Analysis skill** for systematic, evidence-based exploration of unfamiliar repositories
- **Problem Analysis skill** for root cause identification with confidence scoring
- **Decision Critic skill** for adversarial stress-testing of architectural choices
- **Prompt Engineer skill** for systematic prompt optimization grounded in academic literature, with a library of 100+ referenced papers
- **Doc Sync skill** for bootstrapping and maintaining the CLAUDE.md/README.md documentation hierarchy
- **Incoherence Detection skill** for finding spec-vs-implementation mismatches
- **Shared Python library** (`skills/lib/workflow/`) providing sub-agent dispatch templates, step formatting, and workflow metadata
- **Convention system** defining code quality standards, documentation format, severity levels, intent markers, and temporal comment rules
- **Five named agents** (architect, developer, quality-reviewer, technical-writer, debugger) with detailed role definitions and boundaries
- **CI/CD** via GitHub Actions running pytest on every push to `skills/scripts/`

---

## Folder Structure

```
claude-config/
├── .github/
│   ├── CLAUDE.md                    # Index for .github/ directory
│   └── workflows/
│       ├── CLAUDE.md                # Index for workflows/ directory
│       └── skills-test.yml          # GitHub Actions CI: runs pytest on skills/scripts/
│
├── agents/                          # Named sub-agent definitions (Claude Code sub-agents)
│   ├── architect.md                 # Architect: design plans, no code writing
│   ├── developer.md                 # Developer: implement specs, no design decisions
│   ├── quality-reviewer.md          # QR: detect production risks and structural debt
│   ├── technical-writer.md          # TW: documentation optimized for LLM consumption
│   └── debugger.md                  # Debugger: evidence-based root cause analysis, no fixes
│
├── conventions/                     # Shared standards for agents and skills
│   ├── CLAUDE.md                    # Index with triggers for each convention file
│   ├── REGISTRY.yaml                # Declarative mapping: agent role -> conventions received
│   ├── documentation.md             # CLAUDE.md/README.md format specification
│   ├── severity.md                  # MUST/SHOULD/COULD severity taxonomy
│   ├── structural.md                # Default code quality conventions (god objects, testing, etc.)
│   ├── temporal.md                  # Timeless Present Rule for code comments
│   ├── intent-markers.md            # :PERF:/:UNSAFE:/:SCHEMA: suppression markers
│   ├── diff-format.md               # Unified diff specification for code changes
│   └── code-quality/                # Eight numbered files defining code quality dimensions
│       ├── CLAUDE.md
│       ├── README.md
│       ├── 01-naming-and-types.md
│       ├── 02-structure-and-composition.md
│       ├── 03-patterns-and-idioms.md
│       ├── 04-repetition-and-consistency.md
│       ├── 05-documentation-and-tests.md
│       ├── 06-module-and-dependencies.md
│       ├── 07-cross-file-consistency.md
│       └── 08-codebase-patterns.md
│
├── output-styles/
│   └── direct.md                    # Output style: direct, no hedging, no educational content
│
├── skills/                          # All skill definitions and Python implementations
│   ├── CLAUDE.md                    # Index with mandatory read-before-modify warning
│   ├── README.md                    # "Book pattern" architecture for skill Python files
│   │
│   ├── planner/                     # Planning + execution workflows (most complex skill)
│   │   ├── CLAUDE.md
│   │   ├── SKILL.md                 # Activation: planning vs execution mode routing
│   │   ├── README.md                # Workflow diagrams, QR loop explanation
│   │   ├── INTENT.md                # Authoritative design spec, state schemas, invariants
│   │   └── resources/               # Plan format templates, JSON schema, explore format
│   │
│   ├── deepthink/                   # Open-ended analytical reasoning (14-step full / 8-step quick)
│   ├── refactor/                    # Technical debt analysis across 10 parallel dimensions
│   ├── codebase-analysis/           # Systematic codebase exploration with sub-agents
│   ├── problem-analysis/            # Root cause identification (5 phases, confidence scoring)
│   ├── decision-critic/             # Adversarial decision stress-testing
│   ├── prompt-engineer/             # Prompt optimization with academic paper library
│   │   ├── papers/                  # 100+ academic papers organized by category
│   │   └── references/              # Distilled technique references loaded during optimization
│   ├── doc-sync/                    # CLAUDE.md/README.md hierarchy audit and sync
│   ├── incoherence/                 # Spec-vs-implementation consistency detection
│   ├── cc-history/                  # Claude Code conversation history analysis (doc-only)
│   │
│   └── scripts/                     # Python package root for all skill implementations
│       ├── pytest.ini
│       ├── tests/                   # Test suite (AST, domain types, workflow structure, etc.)
│       └── skills/
│           ├── lib/                 # Shared library
│           │   ├── conventions.py   # Convention file loading for prompts
│           │   ├── io.py            # File I/O utilities
│           │   └── workflow/        # Core orchestration framework
│           │       ├── core.py      # Workflow, StepDef, Arg metadata types
│           │       ├── types.py     # AgentRole, Confidence, Phase, Routing, Dispatch enums/types
│           │       ├── constants.py # Shared constants
│           │       ├── discovery.py # Workflow discovery via importlib scanning
│           │       ├── cli.py       # CLI helpers for workflow entry points
│           │       ├── ast/         # AST nodes, builder, and renderer for XML step output
│           │       ├── formatters/  # Re-exports from ast/ for backward compatibility
│           │       └── prompts/     # Shared dispatch template library
│           │           ├── step.py        # format_step(): assemble body + invoke_after
│           │           ├── subagent.py    # subagent_dispatch / template_dispatch / roster_dispatch
│           │           └── file.py        # format_file_content(): embed file in prompt
│           │
│           ├── planner/             # Planner skill Python implementation
│           │   ├── orchestrator/    # planner.py (14-step), executor.py (9-step)
│           │   ├── architect/       # Plan design sub-agent scripts
│           │   ├── developer/       # Code implementation sub-agent scripts
│           │   ├── technical_writer/ # Documentation sub-agent scripts
│           │   ├── quality_reviewer/ # QR decompose + verify scripts for each phase
│           │   └── shared/          # Schema, constraints, gates, routing, resources
│           │
│           ├── deepthink/
│           ├── codebase_analysis/
│           ├── decision_critic/
│           ├── doc_sync/
│           ├── incoherence/
│           ├── problem_analysis/
│           ├── prompt_engineer/
│           ├── refactor/
│           └── leon_writing_style/  # Personal writing style matcher (not documented publicly)
```

---

## Core Components

### Agents (`agents/`)

Five named agents are defined as markdown files with YAML frontmatter. Claude Code loads these as sub-agent definitions.

**`architect.md`** (model: opus)
Transforms ambiguous requests into executable plans. Makes all design decisions before code is written. Documents WHY choices were made, what was rejected, and what risks were accepted. Boundaries: writes Code Intent (what to change), not implementation diffs. Does not write documentation. Uses Opus because design decisions require the highest-quality reasoning.

**`developer.md`** (model: sonnet)
Translates architectural specs into code. Follows a plan-before-coding protocol even for implementation tasks. Handles two spec types: detailed (prescribes HOW) and freeform (prescribes WHAT). Has strict prohibitions including RULE 0 security constraints (no `eval()`, no SQL concatenation, no unbounded loops). Refuses to write documentation -- escalates to technical-writer. Returns structured XML output.

**`quality-reviewer.md`** (model: sonnet)
Detects production risks and structural defects using a three-rule hierarchy: RULE 0 (knowledge preservation and unrecoverable failures, MUST severity), RULE 1 (project conformance, SHOULD severity), RULE 2 (structural quality patterns, SHOULD/COULD severity). Uses dual-path verification for MUST findings and open-form questions (not yes/no) to avoid confirmation bias.

**`technical-writer.md`** (model: sonnet)
Produces documentation optimized for LLM consumption. Enforces token budgets (~200 tokens for CLAUDE.md, ~500 for README.md). Applies the Timeless Present Rule: no change-narrative comments. Documents what EXISTS, not what was done to create it. Forbidden from marketing language, hedging words, and restating what code already shows.

**`debugger.md`** (model: sonnet)
Gathers evidence before forming hypotheses. Requires 10+ debug statements and 3+ test inputs before any hypothesis. Never implements fixes (analysis only). Cleans all debug artifacts before submitting the report. Uses standardized `[DEBUGGER:location:line]` prefix on all debug output for reliable grep-based cleanup.

---

### Conventions (`conventions/`)

Conventions are loaded by agents just-in-time based on their role and task phase. The `REGISTRY.yaml` declares which conventions each role receives:

| Role             | Conventions Received                                                         |
|------------------|-----------------------------------------------------------------------------|
| developer        | `diff-format.md`                                                             |
| technical_writer | `temporal.md`, `documentation.md`                                           |
| quality_reviewer | `temporal.md`, `structural.md`, `diff-format.md`, `code-quality/*` (phase-specific) |
| refactor         | `code-quality/*` (mode-specific: design vs code)                            |
| explore          | None (codebase reading only)                                                 |

**`documentation.md`** -- The authoritative specification for the two-file documentation hierarchy. CLAUDE.md is a pure navigation index (tabular format, What + When to read columns, no explanatory prose). README.md captures invisible knowledge (anything NOT visible from reading the code). Defines five tiers of in-code documentation: inline comments, function-level blocks, docstrings, module documentation, and cross-cutting README entries.

**`severity.md`** -- MoSCoW-based severity taxonomy. MUST: unrecoverable if missed (knowledge loss, production reliability). SHOULD: maintainability debt, compounds over time. COULD: auto-fixable, low impact. Also defines progressive de-escalation: COULD findings are dropped after iteration 3, SHOULD after iteration 4.

**`temporal.md`** -- The Timeless Present Rule: code comments must be written as if encountered for the first time, with no knowledge of how code got there. Defines five contamination categories: change-relative language, baseline references, location directives, planning artifacts, and intent leakage. Gives transformation pattern: extract the technical justification, discard the change narrative.

**`intent-markers.md`** -- Three suppression markers for intentional code patterns that would otherwise trigger QR checks: `:PERF:` (performance-critical), `:UNSAFE:` (safety-critical with explicit invariant), `:SCHEMA:` (data contract divergence). Format requires semicolon separator and non-empty `[why]` clause. Invalid markers generate MARKER_INVALID (MUST) findings.

**`code-quality/` (01-08)** -- Eight files defining code quality dimensions from local/single-file scope (naming, structure, patterns) up to cross-file and system-wide scope (module dependencies, cross-file consistency, codebase architecture patterns). Each category contains: principle, grep-hints (abstract exemplars for searching), violations (illustrative patterns with severity), exceptions, and threshold. The refactor skill's explore agents use these as their analytical framework.

---

### Skills (`skills/`)

Skills are invoked by name from Claude Code conversations. Each skill has a `SKILL.md` that Claude reads when activation occurs, instructing it to immediately invoke the corresponding Python script.

#### Planner

The most complex skill. Two workflows:

**Planning Workflow (14 steps, `planner.py`):**

```
Step 1:  plan-init          -- Capture context categories into plan.json skeleton
Step 2:  context-verify     -- Write context.json, self-verify completeness
Step 3:  plan-design-work   -- Dispatch architect sub-agent (plan design)
Step 4:  plan-design-qr-decompose -- Dispatch QR (opus) to create qr-plan-design.json
Step 5:  plan-design-qr-verify    -- Parallel QR agents verify items from qr file
Step 6:  plan-design-qr-route     -- PASS -> step 7 | FAIL -> loop to step 3
Step 7:  plan-code-work     -- Dispatch developer sub-agent (code planning)
Step 8:  plan-code-qr-decompose
Step 9:  plan-code-qr-verify
Step 10: plan-code-qr-route       -- PASS -> step 11 | FAIL -> loop to step 7
Step 11: plan-docs-work     -- Dispatch technical-writer sub-agent
Step 12: plan-docs-qr-decompose
Step 13: plan-docs-qr-verify
Step 14: plan-docs-qr-route       -- PASS -> APPROVED | FAIL -> loop to step 11
```

QR verification is parallelized: items from the decomposition step are grouped and dispatched in parallel to separate QR sub-agents. The orchestrator then tallies PASS/FAIL mechanically -- it is explicitly forbidden from interpreting results.

**Execution Workflow (9 steps, `executor.py`):**

```
Step 1: Execution Planning  -- Analyze plan, group milestones into waves
Step 2: Reconciliation      -- (conditional) Validate existing code against plan
Step 3: Implementation      -- Wave-aware parallel developer dispatch
Step 4: Code QR             -- Post-implementation quality review
Step 5: Code QR Gate        -- PASS -> step 6 | FAIL -> loop to step 3
Step 6: Documentation       -- Technical writer updates CLAUDE.md/README.md
Step 7: Doc QR              -- Documentation quality review
Step 8: Doc QR Gate         -- PASS -> step 9 | FAIL -> loop to step 6
Step 9: Retrospective       -- Present execution summary
```

Waves: milestones at the same dependency depth execute in parallel (multiple Task calls in a single response). Sequential waves execute only after the prior wave completes.

State files written to a temporary directory (`STATE_DIR`):
- `plan.json` -- complete plan (milestones, diffs, code intents, documentation)
- `context.json` -- frozen after step 2; passed to all sub-agents
- `qr-{phase}.json` -- ephemeral; deleted on phase PASS

#### DeepThink

Structured multi-step reasoning for open-ended questions where the answer structure itself is unknown. Two modes auto-detected at step 3:

- **Quick mode (8 steps):** Bypasses sub-agent dispatch. Direct reasoning with S2A context clarification, step-back abstraction, explicit planning, synthesis, and factored verification.
- **Full mode (14 steps):** Launches parallel sub-agents with distinct analytical perspectives (steps 6-11), then synthesizes through agreement patterns.

Both modes use factored verification (generate questions, answer WITHOUT viewing synthesis) to avoid confirmation bias. Iteration cap: 5 refinement cycles.

Academic grounding: S2A (Weston & Sukhbaatar), Step-Back Abstraction (Zheng, ICLR 2024), Plan-and-Solve (Wang, ACL 2023), Analogical Prompting (Yasunaga, ICLR 2024), Chain-of-Verification (Meta, 2023), among others.

#### Refactor

Analyzes code for technical debt across 10 parallel explore agents, each assigned a different code quality category from `conventions/code-quality/`. Each explore agent runs a 5-step sub-workflow: domain context, principle extraction, violation pattern generation, search, synthesis. Results are triaged, clustered by shared root cause, and synthesized into prioritized work items. Does NOT generate refactored code -- produces recommendations only.

#### Codebase Analysis

Six-phase systematic investigation: Exploration (explore sub-agent), Focus Selection (classify areas P1/P2/P3), Investigation Planning (commit to specific files and questions), Deep Analysis (progressive investigation with file:line evidence), Verification (audit completeness), Synthesis (prioritized recommendations). Outputs findings organized by severity (CRITICAL/HIGH/MEDIUM/LOW) with quoted code citations.

#### Problem Analysis

Five-phase root cause identification: Gate (validate single testable problem), Hypothesize (2-4 distinct candidate explanations), Investigate (iterative evidence gathering, max 5 iterations), Formulate (synthesize into root cause), Output (structured report). Root causes must be framed as conditions that exist, not absences of solutions. Confidence derived from four factual criteria (evidence, alternatives, explanation, framing) -- not self-reported.

#### Decision Critic

Four-phase adversarial analysis: Decomposition (claims, assumptions, constraints with IDs), Verification (answer questions independently to prevent confirmation bias), Challenge (steel-man argument against, explore alternative framings), Synthesis (STAND/REVISE/ESCALATE verdict). Designed specifically to counter LLM sycophancy.

#### Prompt Engineer

Analyzes prompts against a curated library of 100+ academic papers organized into six categories:
- `context/augmentation/` -- in-context learning, example selection
- `context/reframing/` -- role-play, contrastive prompting, perspective
- `correctness/refinement/` -- prompt chaining, iterative refinement
- `correctness/sampling/` -- self-consistency, ensemble methods
- `correctness/verification/` -- self-refine, chain-of-verification
- `reasoning/decomposition/` -- tree-of-thought, least-to-most, plan-and-solve
- `reasoning/elicitation/` -- chain-of-thought triggers, metacognitive prompting
- `structure/` -- format, calibration, directional stimulus
- `efficiency/` -- concise CoT, batch prompting, token budget

The skill reads these references, analyzes the target prompt, proposes changes with explicit paper attribution and before/after diffs, waits for approval, then applies.

#### Doc Sync

Five-phase hierarchy maintenance: Discovery (map directories, identify missing/outdated CLAUDE.md files), Audit (check for drift), Migration (move architectural content from CLAUDE.md to README.md), Update (create/update indexes), Verification (confirm coverage). Used primarily for bootstrapping or recovery after major refactors. The planning workflow's technical writer handles ongoing maintenance during normal use.

#### Incoherence

21-step interactive workflow in three phases: Detection (steps 1-12, parallel agents survey and verify candidate inconsistencies), Resolution (steps 13-15, interactive AskUserQuestion prompts), Application (steps 16-21, apply changes and present report). Resolution is interactive; no manual file editing required.

#### CC History

Documentation-only skill (no Python scripts). Provides structural knowledge about Claude Code's JSONL conversation history format, path encoding rules, and jq query patterns. Design decision: shell + jq composes better than custom tooling for ad-hoc history analysis.

---

### Shared Library (`skills/scripts/skills/lib/workflow/`)

The core framework shared across all skills.

**`prompts/subagent.py`** -- Three dispatch patterns:
- `subagent_dispatch(agent_type, command, prompt, model)` -- single sequential dispatch
- `template_dispatch(agent_type, template, targets, command)` -- parallel SIMD (same template, N targets with `$var` substitution)
- `roster_dispatch(agent_type, agents, command, shared_context)` -- parallel MIMD (shared context + unique tasks per agent)

**`prompts/step.py`** -- `format_step(body, next_cmd, title)` assembles a complete workflow step. Every step has the same structure: body (prompt content) + invoke_after (command the LLM runs next). Empty `next_cmd` signals terminal step.

**`prompts/file.py`** -- `format_file_content(path, content)` embeds file content in a prompt using 4-backtick fences to handle content containing triple-backticks.

**`types.py`** -- Domain types: `AgentRole` enum, `Confidence` enum, `Phase` enum (design review, diff review, codebase review, refactor design, refactor code), `Mode` enum (design vs code), routing types (`LinearRouting`, `BranchRouting`, `TerminalRouting`), `Dispatch`, `StepGuidance`, `BoundedInt` (for property-based test generation), `QuestionOption`, `UserInputResponse`.

**`core.py`** -- Metadata types for workflow introspection: `StepDef` (id, title, actions), `Workflow` (collection of steps with validation), `Arg` (parameter metadata for CLI arguments). The execution engine was deliberately removed -- skills use CLI-based step invocation, not a runtime engine.

---

### Output Styles (`output-styles/`)

**`direct.md`** -- A communication style definition. No hedging, no apologies, no educational content unless explicitly requested. Forbidden formatting: markdown headers, bullet points in prose, bold/italic, emoji, code blocks for non-code content. Default pattern: one-line summary (optional), technical prose, code with inline WHY comments.

---

## How It Works

### The Step-Based Workflow Engine

All skills are implemented as Python scripts that output a "step" -- a formatted block of instructions the LLM reads and follows, ending with a command to run next (`invoke_after`). The LLM runs the command, receives the next step's instructions, and continues until a terminal step is reached.

```
LLM reads step N output
    -> follows DO instructions
    -> runs NEXT command (python3 -m skills.X.Y --step N+1 ...)
    -> receives step N+1 output
    -> continues until no NEXT command
```

This architecture means:
- Skills are stateless Python scripts (no daemon, no server)
- The LLM's context window IS the execution state between steps
- Scripts can be re-invoked at any step for resume/retry scenarios
- State that must survive context resets is written to JSON files

### Context Hygiene in Practice

Every directory in a project using this workflow has two optional files:

**`CLAUDE.md`** -- Loaded automatically by Claude Code when entering a directory. Contains ONLY a tabular index: file/directory names, what they contain, and when to read them. Token budget: ~200 tokens. The "When to read" column uses task-oriented triggers so the LLM can scan and identify relevant files without loading everything.

**`README.md`** -- Loaded only when the CLAUDE.md trigger says to. Contains invisible knowledge: architectural decisions, invariants, tradeoffs, rejected alternatives -- anything NOT visible from reading the source files. Token budget: ~500 tokens.

The principle: indexes load automatically but stay small. Detailed knowledge loads only when relevant.

### Planning Data Flow

```
User prompt
    |
    v
planner.py --step 1   (creates STATE_DIR, writes plan.json skeleton)
    |
    v
planner.py --step 2   (orchestrator writes context.json from conversation)
    |
    v
planner.py --step 3   (orchestrator dispatches architect sub-agent)
    |
    v
[architect reads context.json, reads project docs, writes plan.json milestones]
    |
    v
planner.py --step 4   (orchestrator dispatches QR decompose: writes qr-plan-design.json)
    |
    v
planner.py --step 5   (orchestrator reads qr file, dispatches parallel QR verify agents)
    |
    v
planner.py --step 6   (orchestrator routes: PASS -> step 7, FAIL -> loop to step 3)
    ... (repeat for code and docs phases) ...
    |
    v
PLAN APPROVED: plan.json translated to plan.md, copied to user's requested path
```

### Execution Data Flow

```
User: "execute plan.md"
    |
    v
executor.py --step 1  (analyze plan, build wave groupings)
    |
    v
executor.py --step 3  (dispatch developer per milestone, wave-aware parallel)
    |
    v
[developer reads plan.json milestone, implements code, returns structured XML]
    |
    v
executor.py --step 4  (dispatch QR code review)
    |
    v
executor.py --step 5 --qr-status pass/fail  (gate: loop or proceed)
    |
    v
executor.py --step 6  (dispatch technical writer: CLAUDE.md/README.md updates)
    |
    v
executor.py --step 7/8  (doc QR gate: loop or proceed)
    |
    v
executor.py --step 9  (retrospective presented to user)
```

### Sub-Agent Dispatch Patterns

The shared library provides three dispatch patterns used throughout skills:

**Sequential (subagent_dispatch):** One agent, one task. Used for work phases where a single specialized agent operates on the current artifact.

**SIMD parallel (template_dispatch):** Same prompt template applied to N targets with `$variable` substitution. Used for QR verification where the same checks run against different milestones.

**MIMD parallel (roster_dispatch):** Shared context plus unique tasks per agent. Used for refactor skill's parallel code smell exploration (same codebase, different quality category per agent) and deepthink's divergent exploration phase (same question, different analytical perspectives).

### Quality Gate Pattern

QR gates follow a consistent pattern across all skills:

1. **Decompose:** One QR agent reads the artifact and writes structured verification items to `qr-{phase}.json`
2. **Verify:** Orchestrator reads the QR file, groups items, and dispatches parallel verification agents -- one per group
3. **Route:** Orchestrator mechanically tallies PASS/FAIL; any FAIL loops back to the work step

The orchestrator is explicitly forbidden from interpreting QR results, claiming "diminishing returns," or proceeding without a PASS verdict.

---

## Usage Guide

### Installation

The framework is designed to be cloned as the `.claude` directory:

```bash
# Per-project installation
git clone https://github.com/solatis/claude-config .claude

# Global installation (new setup)
git clone https://github.com/solatis/claude-config ~/.claude

# Global installation (merge into existing ~/.claude)
cd ~/.claude
git remote add workflow https://github.com/solatis/claude-config
git fetch workflow
git merge workflow/main --allow-unrelated-histories
```

Python 3.11+ and pytest are required to run the test suite:

```bash
cd .claude/skills/scripts
pip install pytest hypothesis
pytest tests/ -v
```

### Standard Workflow for Non-Trivial Changes

**Step 1: Explore** -- Understand the codebase before planning.

```
Use your codebase analysis skill to explore src/ with focus on authentication.
```

**Step 2: Think it through (optional)** -- For analytical questions without a known answer structure.

```
Use your deepthink skill to think through [question]
Use your deepthink skill (quick) to [question]    # explicit quick mode
Use your deepthink skill (full) to [question]     # explicit full mode
```

**Step 3: Plan** -- Write a plan file with full review cycles.

```
Use your planner skill to write a plan to plans/my-feature.md
```

The planner will ask clarifying questions, surface ambiguities, run technical writer and quality reviewer passes, and write the approved plan to the specified file.

**Step 4: Clear context** -- `/clear` -- start fresh. The plan file contains all necessary context.

**Step 5: Execute** -- Run the plan against the codebase.

```
Use your planner skill to execute plans/my-feature.md
```

The planner delegates to developers, runs milestone-by-milestone with quality gates, updates documentation, and presents a retrospective.

### Skill Reference

| Skill | Command | When to Use |
|-------|---------|-------------|
| `planner` | `Use your planner skill to write a plan to X` | Non-trivial features requiring structured planning |
| `planner` | `Use your planner skill to execute X` | Executing an approved plan |
| `deepthink` | `Use your deepthink skill to think through [question]` | Open-ended analytical questions, trade-off analysis |
| `codebase-analysis` | `Use your codebase analysis skill to explore X` | Unfamiliar codebases, security reviews, architecture evaluation |
| `problem-analysis` | `Use your problem analysis skill on [bug description]` | Root cause identification |
| `decision-critic` | `Use your decision critic skill to stress-test [decision]` | Architectural choices, technology selection |
| `refactor` | `Use your refactor skill on src/services/` | Technical debt identification after LLM-generated features |
| `prompt-engineer` | `Use your prompt engineer skill to optimize agents/developer.md` | Improving agent or skill prompts |
| `doc-sync` | `Use your doc-sync skill to synchronize documentation` | Bootstrapping, after major refactors |
| `incoherence` | `Use your incoherence skill to detect mismatches in [area]` | Spec/implementation consistency checks |

### Skill Invocation for All Python-Backed Skills

All Python skill scripts are invoked as modules from the `skills/scripts/` directory:

```bash
python3 -m skills.<skill_name>.<module> --step 1
# Example:
python3 -m skills.problem_analysis.analyze --step 1
python3 -m skills.planner.orchestrator.planner --step 1
python3 -m skills.planner.orchestrator.executor --step 1
```

### Bootstrapping the Documentation Hierarchy on an Existing Repository

For an existing project without CLAUDE.md/README.md files:

```
Use your doc-sync skill to synchronize documentation across this repository
```

For a targeted area:

```
Use your doc-sync skill to update documentation in src/validators/
```

### Adding a New Intent Marker

When code intentionally uses a pattern that would trigger QR checks:

```python
# :PERF: unchecked bounds; loop invariant i<len guarantees safety
items[i] = value

# :UNSAFE: raw pointer dereference; caller contract ensures non-null lifetime
*ptr = compute()

# :SCHEMA: legacy_field unused; migration M-042 pending, rollback requires this field
legacy_field = None
```

---

## Notable Patterns and Design Decisions

### The "Book Pattern" for Skill Files

Skill Python files are organized top-to-bottom in a fixed section order so that a reader never needs to scroll up to understand what they are reading. Sections flow: SHARED PROMPTS -> CONFIGURATION -> SYSTEM PROMPTS -> MESSAGE TEMPLATES -> PARSING FUNCTIONS -> MESSAGE BUILDERS -> DOMAIN LOGIC -> STEP DEFINITIONS -> OUTPUT FORMATTING -> ENTRY POINT.

Within MESSAGE TEMPLATES, constants are organized chronologically by workflow step using step dividers (`# --- STEP N: PHASE_NAME ---`). This prevents forward references within function sections (functions can reference any constant defined above them).

### Prompts as String Constants, Not Function Returns

The framework explicitly forbids "action factories" -- functions that return prompt fragments. Prompt text must be visible at constant definition sites. The only exception is complex conditional logic that genuinely requires a function. This makes prompts auditable and prevents the cognitive overhead of tracing through function call chains to understand what text is actually being sent to the model.

### Strings as Parenthesized Concatenation

Multi-line prompt strings use parenthesized line-by-line concatenation rather than triple-quoted strings. This keeps content at its proper indentation level and makes blank lines explicit (`"\n"` on its own line). Triple-quoted strings force column 0 indentation for multi-line content.

### Just-in-Time Convention Loading

Conventions are not loaded at agent startup. They are referenced via `<file working-dir=".claude" uri="conventions/X.md" />` tags in agent definitions and loaded only when the agent's task matches the convention's trigger. The `REGISTRY.yaml` documents which conventions each role receives, and CI validates that actual `get_convention()` calls in scripts match these declarations.

### Orchestrator Never Writes Code

The planner orchestrator is designed to never directly write, read, or modify code or plan content. It dispatches to specialized sub-agents (architect, developer, technical-writer, quality-reviewer) and routes based on their outputs. This separation produces cleaner delegation boundaries and prevents the orchestrator from accumulating implementation concerns.

### Per-Phase QR Files Over Single QA File

Each QR phase writes to its own `qr-{phase}.json` file rather than a shared `qa.json`. This prevents cross-phase contamination (plan QR items mixing with implementation QR items), makes verification scope unambiguous, and enables each phase to have an independent verification cycle. Files are deleted when their phase passes the QR gate.

### Confidence from Factual Criteria, Not Self-Report

Both DeepThink and Problem Analysis derive confidence levels from specific factual questions about the analysis rather than asking the model "how confident are you?" -- which produces unreliable self-reported values due to lack of calibrated introspective access. This pattern is grounded in the Chain-of-Verification research showing independent verification accuracy (70%) vs yes/no confirmation bias (17%).

### Separate Decompose and Verify Steps in QR

QR is split into a decompose step (one agent creates structured verification items) and a verify step (multiple parallel agents verify items independently). The decompose step runs exactly once per phase; if `qr-{phase}.json` already exists (retry scenario), decomposition is skipped. This design means QR items are defined by a focused agent with full context, then verified in parallel without that agent's potential biases.

### Progressive De-escalation in QR Severity

QR findings use progressive de-escalation across retry iterations: COULD findings are only reported in iterations 1-3, SHOULD findings in iterations 1-4, MUST findings in all iterations. This prevents QR loops from running indefinitely on cosmetic issues while ensuring critical knowledge-loss findings always block.

### Two-Invoke Concept

The framework distinguishes two types of "invoke" in step output: the sub-agent invoke (inside a dispatch prompt, telling the spawned agent what command to run) and the parent invoke_after (at the end of the step, telling the current agent what to run next after sub-agents return). A dispatch step has both. This separation prevents confusion about which agent is being instructed.
