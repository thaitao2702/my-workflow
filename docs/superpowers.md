# Superpowers — Comprehensive Documentation

**Version:** 5.0.5 (as of March 2026)
**Author:** Jesse Vincent / Prime Radiant
**Source:** `E:/Project/My Workflow/superpowers/`
**Repository:** https://github.com/obra/superpowers

---

## Table of Contents

1. [Overview / Purpose](#overview--purpose)
2. [Key Features](#key-features)
3. [Folder Structure](#folder-structure)
4. [Core Components](#core-components)
5. [How It Works](#how-it-works)
6. [The Basic Workflow (End-to-End)](#the-basic-workflow-end-to-end)
7. [Skills Reference](#skills-reference)
8. [Platform Support and Installation](#platform-support-and-installation)
9. [Usage Guide](#usage-guide)
10. [Testing Infrastructure](#testing-infrastructure)
11. [Design Philosophy and Notable Patterns](#design-philosophy-and-notable-patterns)

---

## Overview / Purpose

Superpowers is a complete software development workflow framework delivered as a plugin for AI coding agents. Rather than letting agents write code impulsively, it installs a set of composable **"skills"** — structured process guides — that the agent is instructed to follow before responding to any task.

The core idea: when you fire up your coding agent and describe something you want to build, Superpowers ensures the agent **doesn't just start coding**. Instead it steps back, asks clarifying questions, refines a spec, creates a structured implementation plan, then executes that plan through subagents with multi-stage code review at each step. The process enforces Test-Driven Development, systematic debugging, and evidence-based completion throughout.

Because skills trigger automatically based on the user's intent, the user does not need to remember to invoke them — the agent just has Superpowers.

**Platforms supported:** Claude Code (official marketplace), Cursor, OpenCode, Codex, and Gemini CLI.

---

## Key Features

- **Automatic skill activation** — the agent checks for relevant skills before any response. Skills trigger on intent, not explicit user commands.
- **Structured design-first workflow** — brainstorming produces a spec document before any code is written; specs go through an automated review loop.
- **Bite-sized implementation plans** — every task broken into 2–5 minute steps with exact file paths, full code, and expected test output.
- **Subagent-driven execution** — a fresh subagent per task, with two-stage review (spec compliance first, code quality second) after each task.
- **Enforced TDD** — Red-Green-Refactor is mandatory; code written before the failing test must be deleted and rewritten.
- **Systematic debugging** — four-phase root-cause process; patches without investigation are forbidden.
- **Verification before completion** — every success claim must be backed by a freshly-run command whose output is shown.
- **Git worktree isolation** — all feature work happens on a dedicated branch in an isolated worktree.
- **Visual brainstorming companion** — optional browser-based server for showing mockups and diagrams during the design phase.
- **Multi-platform plugin architecture** — same skill library works across Claude Code, Cursor, Codex, OpenCode, and Gemini CLI.
- **Extensible** — users can write their own skills following the same format and TDD-for-documentation approach.

---

## Folder Structure

```
superpowers/
├── .claude-plugin/          # Claude Code plugin manifest
│   ├── plugin.json          # Plugin metadata (name, version, author)
│   └── marketplace.json     # Dev marketplace definition
│
├── .cursor-plugin/          # Cursor plugin manifest
│   └── plugin.json          # Points to skills/, agents/, commands/, hooks
│
├── .opencode/               # OpenCode plugin
│   ├── INSTALL.md           # Manual install instructions
│   └── plugins/superpowers.js  # JS plugin that injects bootstrap + registers skills
│
├── .codex/                  # Codex setup
│   └── INSTALL.md           # Clone + symlink instructions
│
├── .github/                 # GitHub issue/PR templates
│
├── agents/
│   └── code-reviewer.md     # Agent definition for the code-reviewer subagent
│
├── commands/                # Deprecated slash commands (now point to skills)
│   ├── brainstorm.md
│   ├── write-plan.md
│   └── execute-plan.md
│
├── hooks/
│   ├── hooks.json           # Claude Code hook config (SessionStart)
│   ├── hooks-cursor.json    # Cursor hook config
│   ├── session-start        # Bash script: injects using-superpowers into session
│   └── run-hook.cmd         # Cross-platform polyglot wrapper for Windows support
│
├── skills/                  # The core library — one subdirectory per skill
│   ├── using-superpowers/   # Bootstrap skill (loaded on every session start)
│   ├── brainstorming/       # Design-first ideation and spec writing
│   ├── writing-plans/       # Implementation plan creation
│   ├── subagent-driven-development/  # Primary execution engine
│   ├── executing-plans/     # Alternate execution (no subagents)
│   ├── test-driven-development/      # TDD enforcement
│   ├── systematic-debugging/         # Root-cause debugging process
│   ├── verification-before-completion/  # Evidence-before-claims rule
│   ├── requesting-code-review/       # Dispatch code reviewer subagent
│   ├── receiving-code-review/        # How to respond to review feedback
│   ├── using-git-worktrees/          # Isolated workspace setup
│   ├── finishing-a-development-branch/  # Merge/PR/discard workflow
│   ├── dispatching-parallel-agents/  # Concurrent subagent patterns
│   └── writing-skills/               # Meta: how to create new skills
│
├── docs/
│   ├── README.codex.md      # Codex-specific docs
│   ├── README.opencode.md   # OpenCode-specific docs
│   ├── testing.md           # Integration test documentation
│   ├── windows/             # Windows-specific technical notes
│   └── plans/ and superpowers/   # Design plans and specs for the project itself
│
├── tests/                   # Test suites for the framework itself
│   ├── brainstorm-server/   # Unit tests for the visual companion server
│   ├── claude-code/         # Integration tests (run real Claude sessions)
│   ├── explicit-skill-requests/  # Prompts + scripts for triggering skills
│   ├── opencode/            # OpenCode plugin tests
│   ├── skill-triggering/    # Tests that specific prompts trigger correct skills
│   └── subagent-driven-dev/ # End-to-end subagent development test fixtures
│
├── gemini-extension.json    # Gemini CLI extension metadata
├── GEMINI.md                # Gemini context file (loads using-superpowers + tool map)
├── package.json             # npm package (main = OpenCode plugin entry)
├── README.md
├── CHANGELOG.md
└── LICENSE                  # MIT
```

---

## Core Components

### `hooks/session-start` + `hooks/run-hook.cmd`

These two files are the **entry point** for every session. When a new Claude Code or Cursor session starts, the `SessionStart` hook fires:

1. `run-hook.cmd` is a cross-platform **polyglot script** — valid in both Windows CMD and bash simultaneously. On Windows it finds Git Bash and delegates to it. On Unix it runs directly.
2. `session-start` (bash) reads the content of `skills/using-superpowers/SKILL.md` and injects it into the session context as an `<EXTREMELY_IMPORTANT>` block.

The result: every session begins with the agent already knowing the rule system — check for skills before responding to anything.

### `skills/using-superpowers/SKILL.md`

The **bootstrap skill**. Loaded automatically at session start, it establishes:
- The absolute rule: invoke any skill with even a 1% chance of relevance before responding.
- How to invoke skills on each platform (the `Skill` tool in Claude Code, `activate_skill` in Gemini CLI, etc.).
- Instruction priority: user's CLAUDE.md/GEMINI.md/AGENTS.md instructions always outrank skills.
- A decision flowchart for when to invoke which skill.
- A "Red Flags" table listing rationalizations that indicate the agent is about to skip a skill.

This skill is intentionally loaded into every session — it is the kernel of the system.

### `skills/brainstorming/SKILL.md`

The **design phase skill**. Triggers before any creative/implementation work. Its enforced checklist:

1. Explore existing project context (files, docs, recent commits).
2. Optionally offer the Visual Companion for visual questions.
3. Ask clarifying questions one at a time.
4. Propose 2–3 approaches with trade-offs.
5. Present design in sections, get user approval after each section.
6. Write spec to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` and commit.
7. Run automated spec review loop (dispatch `spec-document-reviewer` subagent).
8. Ask user to review the written spec.
9. Invoke `writing-plans` skill.

A hard gate prevents any implementation work until the user approves the design.

#### Visual Companion (`skills/brainstorming/visual-companion.md` + `scripts/`)

An optional browser-based companion that serves HTML mockups during brainstorming. The agent writes HTML fragments to a directory; a Node.js WebSocket server (`server.cjs`) watches for new files and pushes them to the browser in real time. User clicks are recorded to a `.events` file the agent reads on its next turn.

The server is zero-dependency (implements WebSocket from scratch using Node's built-in `crypto` and `http` modules). It auto-detects Windows and skips PID-based lifecycle monitoring (which doesn't work in MSYS2), relying on a 30-minute idle timeout instead.

### `skills/writing-plans/SKILL.md`

Produces the **implementation plan document**. Every plan must:
- Start with a standard header including goal, architecture summary, and tech stack.
- Map out all files to be created/modified before defining tasks.
- Break each task into 2–5 minute steps with the exact test code, implementation code, run commands, expected output, and git commit.
- Be saved to `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`.
- Pass a plan-document-reviewer subagent review loop.

After the plan is written, the user chooses between:
- **Subagent-Driven Development** (recommended) — fresh subagent per task in the same session.
- **Inline Execution** — the current session executes tasks directly with `executing-plans`.

### `skills/subagent-driven-development/SKILL.md`

The **primary execution engine**. Orchestrates plan execution using a controller + subagent pattern:

For each task in the plan:
1. Dispatch an **implementer subagent** with the full task text (never makes the subagent read the file — text is provided directly). Implementer follows TDD, commits work, performs self-review, reports back with status `DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT`.
2. Dispatch a **spec compliance reviewer subagent** — verifies code matches the spec (not the implementer's report, the actual code). Flags missing or extra features.
3. If issues: implementer fixes → spec reviewer re-reviews (loop).
4. Dispatch a **code quality reviewer subagent** — checks code quality, test coverage, naming, file size. Uses the `code-reviewer` agent template.
5. If issues: implementer fixes → code quality reviewer re-reviews (loop).
6. Mark task complete in TodoWrite.

After all tasks: dispatch a final code reviewer, then invoke `finishing-a-development-branch`.

The controller selects the cheapest model that can handle each subtask, preserving cost.

### Prompt Templates (inside `skills/subagent-driven-development/`)

| File | Purpose |
|---|---|
| `implementer-prompt.md` | Template for dispatching a task implementer subagent |
| `spec-reviewer-prompt.md` | Template for spec compliance review — instructs reviewer to distrust implementer's report and read code directly |
| `code-quality-reviewer-prompt.md` | Template for code quality review using the `code-reviewer` agent |

### `skills/test-driven-development/SKILL.md`

The **TDD enforcement skill**. Defines the Iron Law: no production code without a failing test first. If code was written before the test, delete it and start over — no "keeping as reference," no adapting while writing tests. The skill includes:
- The full Red-Green-Refactor cycle with verification steps.
- Good/bad code examples.
- A rationalization table countering every common excuse.
- A verification checklist agents must tick before marking work complete.

Companion: `testing-anti-patterns.md` — covers five anti-patterns (testing mock behavior, test-only methods in production code, mocking without understanding dependencies, incomplete mocks, tests as afterthought).

### `skills/systematic-debugging/SKILL.md`

A **four-phase debugging process** that must complete before any fix is attempted:

| Phase | Key Activities |
|---|---|
| 1. Root Cause Investigation | Read errors, reproduce, check recent changes, add instrumentation at every component boundary, trace data flow |
| 2. Pattern Analysis | Find working examples, compare against references, list every difference |
| 3. Hypothesis & Testing | Form a single hypothesis, make the smallest possible change to test it |
| 4. Implementation | Create failing test, implement fix, verify |

After 3+ failed fixes the skill escalates to questioning the architecture rather than continuing to patch. Companion files: `root-cause-tracing.md` (backward stack trace technique), `defense-in-depth.md` (validation at all four layers), `condition-based-waiting.md` (replace arbitrary timeouts with condition polling).

### `skills/verification-before-completion/SKILL.md`

Enforces **evidence before claims**. Any claim that work is complete, tests pass, or a bug is fixed must be preceded by running the verification command in that same message and showing the output. Claiming success based on memory of a previous run, agent reports, or "should work now" reasoning is treated as dishonesty.

### `skills/using-git-worktrees/SKILL.md`

Creates an **isolated git worktree** before any implementation begins. Priority for worktree directory: existing `.worktrees/` > existing `worktrees/` > CLAUDE.md preference > ask user. Verifies the directory is in `.gitignore` before creating the worktree, then auto-detects and runs project setup (`npm install`, `cargo build`, `pip install`, etc.), and verifies a clean test baseline. Never proceeds with failing tests without explicit user consent.

### `skills/finishing-a-development-branch/SKILL.md`

Guides branch completion. Verifies tests pass, then presents exactly four options: merge locally, push and create PR, keep as-is, or discard. Each option has a specific sequence of git commands. Discard requires typing "discard" as confirmation. Cleans up the worktree for options 1 and 4 only.

### `skills/requesting-code-review/SKILL.md` + `agents/code-reviewer.md`

Dispatches a **`code-reviewer` subagent** with a precisely-crafted prompt (never the session's chat history). The `code-reviewer` agent is defined in `agents/code-reviewer.md` and performs: plan alignment analysis, code quality assessment, architecture review, documentation check, and categorized issue reporting (Critical / Important / Suggestion).

### `skills/receiving-code-review/SKILL.md`

Rules for **responding to code review feedback**: verify before implementing, ask before assuming, push back with technical reasoning when feedback is wrong, apply changes one at a time, no performative agreement ("You're absolutely right!" is forbidden). External reviewer feedback is a suggestion to evaluate, not an order to follow.

### `skills/dispatching-parallel-agents/SKILL.md`

When multiple independent problems exist (e.g., 3 test files failing for unrelated reasons), dispatch one agent per domain simultaneously rather than investigating sequentially. Covers: identifying independent domains, writing focused agent prompts with specific scope and output requirements, reviewing and integrating results. Includes a real example where 6 failures across 3 files were fixed in parallel in the time it would have taken to fix 1 sequentially.

### `skills/writing-skills/SKILL.md`

The **meta skill** for creating new skills. Applies TDD to documentation:
- RED: run a pressure scenario with a subagent _without_ the skill to document baseline violations.
- GREEN: write the skill addressing those specific rationalizations.
- REFACTOR: find new loopholes agents use, add explicit counters, re-test.

Defines skill structure (YAML frontmatter with `name` and `description` only), Claude Search Optimization (CSO) principles, token efficiency targets, flowchart usage rules, and a full deployment checklist. Key insight: the `description` field must describe triggering conditions only — never summarize the skill's workflow, because doing so causes the agent to follow the description shortcut instead of reading the full skill body.

### `.opencode/plugins/superpowers.js`

A JavaScript ES module plugin for OpenCode. On load it:
1. Appends the superpowers `skills/` directory to OpenCode's `config.skills.paths` so all skills are discoverable without symlinks.
2. Injects the `using-superpowers` skill content plus a tool-mapping table into the system prompt via the `experimental.chat.system.transform` hook.

### `GEMINI.md`

The Gemini CLI context file. Contains two `@` file references: `skills/using-superpowers/SKILL.md` (loads the bootstrap) and `skills/using-superpowers/references/gemini-tools.md` (maps Claude Code tool names to Gemini CLI equivalents, and notes that Gemini has no subagent support).

---

## How It Works

### Session Bootstrap

When a session starts:

```
Claude Code / Cursor
    → hooks/hooks.json fires SessionStart hook
    → hooks/run-hook.cmd (cross-platform dispatcher)
    → hooks/session-start (bash)
    → reads skills/using-superpowers/SKILL.md
    → injects content into session as <EXTREMELY_IMPORTANT> context

Gemini CLI
    → reads GEMINI.md at session start
    → GEMINI.md includes using-superpowers via @ reference

OpenCode
    → loads .opencode/plugins/superpowers.js
    → plugin injects bootstrap via system prompt transform hook

Codex
    → skills symlinked into ~/.agents/skills/superpowers/
    → Codex discovers and loads skills natively
```

### Skill Invocation Flow

Once the bootstrap is loaded, every agent turn follows this decision graph (defined in `using-superpowers/SKILL.md`):

```
User message received
    → Might any skill apply? (even 1% chance)
        → YES: Invoke Skill tool → Announce "Using [skill] to [purpose]"
               → Has checklist? → Create TodoWrite todos → Follow skill exactly
        → Definitely not: Respond
    → About to enter plan mode?
        → Already brainstormed?
            → NO: Invoke brainstorming skill first
```

### The Full Development Lifecycle

```
1. User: "I want to build X"
   → brainstorming skill triggers
   → Agent asks clarifying questions, proposes approaches, presents design
   → Spec written to docs/superpowers/specs/
   → Automated spec review loop (spec-document-reviewer subagent)
   → User approves spec

2. → writing-plans skill triggers
   → Agent maps files, breaks work into 2-5 min TDD steps
   → Plan written to docs/superpowers/plans/
   → Automated plan review loop (plan-document-reviewer subagent)
   → User approves plan

3. → using-git-worktrees skill triggers
   → New branch + isolated worktree created
   → Dependencies installed, baseline tests verified

4. User chooses execution mode:
   → subagent-driven-development (recommended):
       For each task:
         → implementer subagent (TDD, self-review, commit)
         → spec compliance reviewer subagent
         → [fix loop if needed]
         → code quality reviewer subagent
         → [fix loop if needed]
         → TodoWrite task marked complete
       → final code reviewer

   → OR executing-plans (inline):
       Agent executes each task step-by-step in current session
       Stops and asks when blocked

5. → finishing-a-development-branch skill triggers
   → Tests verified
   → User chooses: merge locally / create PR / keep / discard
   → Worktree cleaned up
```

### Data Flow in Subagent-Driven Development

The controller (main session) reads the plan file **once** at the start, extracts all task text, and provides full task content directly to each subagent. Subagents never read the plan file themselves — this eliminates file-reading overhead and ensures the controller controls exactly what context each subagent receives.

Subagents are isolated: they get only their task description, architectural context, and working directory. They never inherit the session's conversation history. This prevents context pollution across tasks.

---

## The Basic Workflow (End-to-End)

| Step | Skill | Trigger | Output |
|---|---|---|---|
| 1 | `brainstorming` | Before writing any code | Spec document in `docs/superpowers/specs/` |
| 2 | `using-git-worktrees` | After design approval | Isolated branch + worktree, clean test baseline |
| 3 | `writing-plans` | With approved design | Plan document in `docs/superpowers/plans/` |
| 4a | `subagent-driven-development` | With approved plan (recommended) | Implemented + reviewed + committed code |
| 4b | `executing-plans` | With approved plan (alternative) | Same, executed inline |
| 5 | `test-driven-development` | During any implementation | TDD cycle enforced per task |
| 6 | `requesting-code-review` | Between tasks / before merge | Categorized issues from code-reviewer |
| 7 | `finishing-a-development-branch` | When all tasks complete | Merged/PR'd/kept/discarded branch |

The agent checks for relevant skills before **any** task. These are mandatory workflows, not suggestions.

---

## Skills Reference

### Testing

| Skill | When It Triggers | What It Enforces |
|---|---|---|
| `test-driven-development` | Before writing any implementation code | RED-GREEN-REFACTOR; code before test must be deleted |
| `verification-before-completion` | Before claiming work is done | Run verification command, show output, then claim |

### Debugging

| Skill | When It Triggers | What It Enforces |
|---|---|---|
| `systematic-debugging` | On any bug, test failure, or unexpected behavior | Four-phase root-cause process before any fix |
| `verification-before-completion` | Before claiming a bug is fixed | Fresh test run with output shown |

### Collaboration / Workflow

| Skill | When It Triggers | What It Enforces |
|---|---|---|
| `brainstorming` | Before any creative/build work | Design-first; no code until spec approved |
| `writing-plans` | After spec approval | Bite-sized TDD tasks with exact code |
| `subagent-driven-development` | With an approved plan | Fresh subagent + two-stage review per task |
| `executing-plans` | With an approved plan (no subagents) | Step-by-step plan execution with stop-on-block |
| `dispatching-parallel-agents` | 2+ independent problems | Concurrent agent dispatch |
| `requesting-code-review` | After task completion / before merge | code-reviewer subagent with precise context |
| `receiving-code-review` | When receiving review feedback | Verify before implementing; push back technically |
| `using-git-worktrees` | Before any feature implementation | Isolated workspace setup |
| `finishing-a-development-branch` | When all tasks complete | Test verification + 4-option branch disposition |

### Meta

| Skill | When It Triggers | What It Enforces |
|---|---|---|
| `using-superpowers` | Every session start (auto-loaded) | Skill invocation rules |
| `writing-skills` | When creating/editing skills | TDD-for-documentation; test before deploying |

---

## Platform Support and Installation

### Claude Code (Official Marketplace)

```bash
/plugin install superpowers@claude-plugins-official
```

Or via the development marketplace:
```bash
/plugin marketplace add obra/superpowers-marketplace
/plugin install superpowers@superpowers-marketplace
```

### Cursor

```
/add-plugin superpowers
```

Or search "superpowers" in the Cursor plugin marketplace.

### OpenCode

Add to `opencode.json`:
```json
{
  "plugin": ["superpowers@git+https://github.com/obra/superpowers.git"]
}
```

Restart OpenCode. The plugin installs via Bun and registers skills automatically.

### Codex

```bash
# Clone
git clone https://github.com/obra/superpowers.git ~/.codex/superpowers

# Symlink skills
mkdir -p ~/.agents/skills
ln -s ~/.codex/superpowers/skills ~/.agents/skills/superpowers
```

Restart Codex. Enable multi-agent support in `~/.codex/config.toml`:
```toml
[features]
multi_agent = true
```

### Gemini CLI

```bash
gemini extensions install https://github.com/obra/superpowers
gemini extensions update superpowers  # to update
```

### Tool Name Mapping by Platform

Skills are written using Claude Code tool names. Other platforms use equivalents:

| Claude Code | Gemini CLI | Codex | OpenCode |
|---|---|---|---|
| `Skill` | `activate_skill` | native | native `skill` tool |
| `Task` (subagent) | not supported | `spawn_agent` | `@mention` |
| `TodoWrite` | `write_todos` | `update_plan` | `todowrite` |
| `Read/Write/Edit/Bash` | `read_file` / `write_file` / `replace` / `run_shell_command` | native | native |

**Note:** Gemini CLI has no subagent support. Skills that use subagents (`subagent-driven-development`, `dispatching-parallel-agents`) fall back to single-session `executing-plans` mode.

---

## Usage Guide

### First Use

1. Install the plugin on your chosen platform (see above).
2. Start a new session.
3. Ask to build something: "Help me build a REST API for managing tasks."
4. The agent will automatically invoke `brainstorming` and begin asking clarifying questions.
5. Approve the spec when presented.
6. The agent creates an implementation plan.
7. Approve the plan and choose an execution mode.
8. Watch the agent work through the tasks autonomously.

### Verifying Installation

After installation, start a new session and ask:

```
Tell me about your superpowers
```

The agent should describe the skills system and its workflow.

### Configuration Precedence

Skills are overridden by user instructions:

1. **User instructions** (CLAUDE.md, GEMINI.md, AGENTS.md, direct requests) — highest priority
2. **Superpowers skills** — override default agent behavior
3. **Default agent system prompt** — lowest priority

If `CLAUDE.md` says "skip TDD for this project," the agent follows that instruction even when `test-driven-development` would otherwise trigger.

### Custom and Personal Skills

- **Claude Code:** Place personal skills in `~/.claude/skills/`
- **OpenCode:** Place skills in `~/.config/opencode/skills/` (personal) or `.opencode/skills/` (project)
- **Codex:** Place skills in `~/.agents/skills/`

Custom skills follow the same `SKILL.md` format with YAML frontmatter (`name`, `description`). See `skills/writing-skills/SKILL.md` for the complete guide to writing skills.

### Project-Specific Overrides

For project-specific conventions, add a `CLAUDE.md` (or `GEMINI.md` / `AGENTS.md`) at the project root. The agent reads this on session start and the instructions take precedence over all skills.

### Updating

```bash
# Claude Code
/plugin update superpowers

# Gemini CLI
gemini extensions update superpowers

# OpenCode — automatic on restart

# Codex
cd ~/.codex/superpowers && git pull
```

---

## Testing Infrastructure

The framework tests itself using real agent sessions.

### Integration Tests (`tests/claude-code/`)

Run headless Claude Code sessions and parse the `.jsonl` session transcript to verify:
- The correct skill was invoked (`Skill` tool call present).
- Subagents were dispatched (`Task` tool calls present).
- `TodoWrite` was used for task tracking.
- Implementation files were actually created.
- Tests pass.
- Git commits follow the expected pattern.

Run time: 10–30 minutes per test (real agent sessions).

### Skill Triggering Tests (`tests/skill-triggering/`)

Each file in `prompts/` contains a message that should trigger a specific skill. The test runner checks whether the agent actually invokes that skill before responding.

### Explicit Skill Request Tests (`tests/explicit-skill-requests/`)

Tests verifying the agent correctly invokes a skill when the user explicitly asks for it (e.g., "use subagent-driven-development for this").

### Visual Companion Server Tests (`tests/brainstorm-server/`)

Unit tests for the zero-dependency WebSocket server (`server.cjs`): server lifecycle, WebSocket protocol compliance, file watching, Windows PID behavior.

### Token Analysis Tool

```bash
python3 tests/claude-code/analyze-token-usage.py \
  ~/.claude/projects/<project-dir>/<session-id>.jsonl
```

Shows per-subagent token usage and cost. Useful for understanding the cost profile of subagent-driven development.

---

## Design Philosophy and Notable Patterns

### Skills as Process Documentation, Not Configuration

Skills are markdown files with YAML frontmatter — readable by humans and injected into agent context on demand. They are not code hooks or runtime rules. The agent reads the skill and follows it through reasoning and judgment, which means skills can express nuanced guidelines, handle edge cases, and adapt to context in ways that rigid configuration cannot.

### TDD Applied to Documentation

The `writing-skills` skill establishes that creating a skill follows the same discipline as writing code: run a pressure test without the skill first (RED), write the skill to address observed failures (GREEN), find new loopholes and close them (REFACTOR). This prevents the common failure mode of documentation that sounds correct but doesn't change agent behavior under pressure.

### Claude Search Optimization (CSO)

The `description` field of each skill's YAML frontmatter serves as the index that determines when the agent loads a skill. The key insight (discovered through testing): if the description summarizes the skill's workflow, the agent will follow the description instead of reading the full skill. Descriptions must describe **triggering conditions only**, not workflow summaries. This is counterintuitive but critical.

### Isolated Subagent Context

Subagents never receive the session's chat history. The controller constructs their prompt with exactly the information they need. This prevents context pollution (earlier decisions bleeding into new tasks), reduces token consumption, and makes subagent behavior more predictable.

### Polyglot Hook Script for Windows

`hooks/run-hook.cmd` is syntactically valid in both Windows CMD and Unix bash simultaneously. On Windows, CMD interprets the batch section and finds Git Bash; on Unix, bash ignores the batch section via a heredoc trick and runs directly. This eliminates the need for separate `.bat` and `.sh` files and avoids Claude Code's Windows `.sh` auto-detection interfering with hook execution.

### Zero-Dependency Brainstorm Server

The visual companion server (`skills/brainstorming/scripts/server.cjs`) implements the WebSocket RFC 6455 protocol from scratch using only Node.js built-in modules (`crypto`, `http`, `fs`, `path`). This ensures it works without `npm install` in any project where it is invoked. The server is a CommonJS module (`.cjs`) rather than an ES module to avoid conflict with the root `package.json`'s `"type": "module"` on Node.js 22+.

### Evidence-First Culture

`verification-before-completion` is one of the highest-priority skills. It exists because agents frequently claim success based on reasoning ("this change should fix it") rather than evidence. The skill enforces a discipline of running commands and showing output before making any success claim. This is described as an honesty principle, not just a quality one.

### YAGNI Ruthlessly

Every workflow in the system — brainstorming, plan writing, implementation — enforces YAGNI (You Aren't Gonna Need It). Spec reviewers flag extra features that weren't requested. The TDD skill restricts implementation to the minimal code to pass the current test. This prevents the common AI coding failure mode of over-engineering.

### Instruction Priority Is Explicit

The framework explicitly states that user instructions outrank all skills. This is stated in `using-superpowers` and built into the session bootstrap. The framework cannot override what the user has explicitly asked for in their project configuration files.

---

## Community and Support

- **Discord:** https://discord.gg/Jd8Vphy9jq
- **Issues:** https://github.com/obra/superpowers/issues
- **Marketplace:** https://github.com/obra/superpowers-marketplace
- **Blog post:** https://blog.fsck.com/2025/10/09/superpowers/
- **Sponsorship:** https://github.com/sponsors/obra

---

*Documentation written from source analysis of superpowers v5.0.4/5.0.5, March 2026.*
