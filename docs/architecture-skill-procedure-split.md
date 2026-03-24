# Architecture: Skill + Agent (Two-Layer)

## The Original Concern

Can functions (skills) invoke each other during a workflow? For example, `/plan` needs to trigger `/analyze` for affected components, and `/execute` needs to trigger `/analyze` for stale docs.

## Verified Answer

**Yes — via the Skill tool.** Research into Claude Code's actual mechanics:

1. **Commands and skills are merged** — both create `/something` slash commands. No functional difference.
2. **Skills are prompts** — they get injected into the main session's context. A skill itself cannot make tool calls.
3. **Claude (main session) CAN invoke skills via the `Skill` tool** — this is a real tool available to Claude.
4. **Subagents CAN invoke skills** if the `Skill` tool is listed in their `tools` field.
5. **Subagents CANNOT spawn other subagents** — this is a hard constraint.

### What this means

Cross-function calls work **if the skill instructs Claude to use the `Skill` tool**:

```
User types /plan
  → /plan SKILL.md loads into main session as prompt
  → Claude follows the instructions
  → Instructions say "use the Skill tool to invoke /analyze"
    → Claude calls Skill tool → /analyze loads → Claude follows it → returns
  → Instructions say "spawn planner agent via Agent tool"
    → Claude spawns agent → agent returns result
```

**No intermediate "procedures" layer needed.** Skills are already the orchestration layer. They just need to instruct Claude to use the `Skill` tool for cross-function calls.

## Architecture: Two Layers

```
┌───────────────────────────────────────────────────────────────┐
│ SKILLS (.claude/skills/{name}/SKILL.md)                       │
│                                                               │
│ Each skill contains:                                          │
│ 1. Input parsing (what args does the user pass)               │
│ 2. Full orchestration logic (step-by-step instructions)       │
│ 3. Cross-function calls (via Skill tool)                      │
│ 4. Agent dispatching (via Agent tool)                         │
│                                                               │
│ Invocable by:                                                 │
│ - User typing /name                                           │
│ - Claude using the Skill tool (cross-function calls)          │
│ - Subagents using the Skill tool (if in their tools list)     │
└───────────────────────────────┬───────────────────────────────┘
                                │ spawns via Agent tool
                                ▼
┌───────────────────────────────────────────────────────────────┐
│ AGENTS (.claude/agents/{name}.md)                             │
│                                                               │
│ Focused workers — single-purpose, one goal per agent.         │
│ Spawned by main session (while following a skill).            │
│ CAN invoke skills (if Skill tool in their tools list).        │
│ CANNOT spawn other agents (hard constraint).                  │
└───────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
.claude/
├── skills/                       ← Orchestration + user entry points
│   ├── init/SKILL.md             ← Project initialization
│   ├── plan/SKILL.md             ← Planning orchestration
│   │                                (uses Skill tool → /analyze, /template-apply)
│   ├── execute/SKILL.md          ← Execution orchestration
│   │                                (uses Skill tool → /analyze, /doc-update)
│   ├── analyze/SKILL.md          ← Component analysis orchestration
│   ├── template-create/SKILL.md  ← Template extraction
│   ├── template-apply/SKILL.md   ← Template application
│   │                                (output feeds into /plan or /execute)
│   ├── doc-update/SKILL.md       ← Doc update assessment + action
│   │                                (uses Skill tool → /analyze if MAJOR change)
│   ├── review/SKILL.md           ← Plan/code review
│   └── jira/
│       ├── SKILL.md              ← Jira ticket fetch
│       └── jira_fetch.py
│
├── agents/                       ← Focused workers
│   ├── planner.md                ← Creates phased plan from requirements
│   ├── reviewer.md               ← Reviews plan/code against criteria
│   ├── executor.md               ← Implements one task (TDD)
│   ├── analyzer.md               ← Deep component analysis
│   ├── doc-updater.md            ← Assesses change significance
│   ├── template-extractor.md     ← Extracts pattern from source code
│   └── template-applier.md       ← Fills template variables
│
├── scripts/                      ← CLI tools
│   └── workflow_cli.py           ← Plan/phase/state JSON read/write CLI
│
├── rules/                        ← Passive context (always loaded)
│   ├── quality-criteria.md
│   ├── tdd-policy.md
│   ├── security-gates.md
│   └── resume-protocol.md
│
├── hooks/                        ← Lifecycle hooks
│   ├── pre_tool_use.py
│   ├── post_tool_use.py
│   └── context_monitor.py
│
└── settings.json
```

### Key change from original plan
- `/template` split into two skills: `/template-create` and `/template-apply` — cleaner invocation, and `/plan` only needs to call `/template-apply` (not parse a mode flag)
- `/doc-update` extracted as its own skill — `/execute` calls it via Skill tool after each phase, and it can call `/analyze` if needed

## Cross-Function Call Map

```
/plan
├── Skill tool → /analyze          (Step B: pre-planning component analysis)
├── Skill tool → /template-apply   (Step A.5: if template match found)
├── Agent tool → planner.md        (Step C: create plan)
└── Agent tool → reviewer.md       (Step D: review plan)

/execute
├── Skill tool → /analyze          (Step 2a: stale component docs)
├── Skill tool → /doc-update       (Step 2e: post-phase doc updates)
├── Agent tool → executor.md       (Step 2: implement tasks)
└── Agent tool → reviewer.md       (Step 2d: phase review)

/template-create
└── Agent tool → template-extractor.md

/template-apply
└── Agent tool → template-applier.md
    (output feeds into /plan or /execute — user chooses)

/doc-update
├── Skill tool → /analyze          (if significance = MAJOR)
└── Agent tool → doc-updater.md

/analyze
├── Skill tool → /analyze          (recursive mode — self-call for dependencies)
└── Agent tool → analyzer.md

/init
└── standalone (no cross-calls)
```

## How a Skill Instructs Cross-Calls

### Example: `/plan` SKILL.md (relevant section)

```markdown
## Step B: Component Analysis

For each component identified as affected by these requirements:

1. Check if `{component}.analysis.md` exists alongside the source
2. If missing or stale (last_commit doesn't match current git log):
   - Use the Skill tool to invoke `/analyze` with the component path
   - Wait for analysis to complete before proceeding
3. Collect all relevant `.analysis.md` content for the planner agent

## Step A.5: Template Discovery

1. Read `.workflow/templates/index.md`
2. Match the requirements text against template trigger_keywords
3. If 2+ keywords match:
   - Tell the user: "Found matching template: {name}"
   - Ask: "Use this template as a starting point?"
   - If yes: use the Skill tool to invoke `/template-apply` with the template name
   - Use the template output as additional context for the planner agent
```

### Example: `/analyze` SKILL.md (relevant section for recursive self-call)

```markdown
## Step 2: Dependency Check (recursive mode only)

For each local dependency that lacks a current `.analysis.md`:
- Use the Skill tool to invoke `/analyze` with the dependency path
- This is a recursive call — the invoked /analyze will handle its own dependencies
- Continue only after all dependency analyses complete
```

## Constraint: Subagents Cannot Spawn Subagents

This affects how agents work:

| If an agent needs to... | Solution |
|------------------------|----------|
| Analyze a component | Agent uses Skill tool → `/analyze` (skill loads into agent's context, agent follows it, but CANNOT spawn analyzer subagent from within) |
| Invoke another worker | **Not possible.** Design agents so they don't need to spawn other agents. |
| Run a sub-workflow | Agent uses Skill tool → the skill's instructions guide the agent, but agent can only do the work itself (no delegation to sub-subagents) |

**Practical implication:** Keep agents focused on single tasks. If a workflow step needs both analysis AND execution, the **skill orchestration** (running in main session) should handle the sequencing — invoke `/analyze` first, then spawn the executor agent with the analysis results.

The main session is the only context that can both invoke skills AND spawn agents freely. Design accordingly.

## Design Decisions

### Decision: Two layers, not three
**Originally proposed:** Skills → Procedures → Agents (three layers)
**Revised to:** Skills → Agents (two layers)

**Why:** The "procedures" layer was invented to solve a problem that doesn't exist. Skills can cross-call via the Skill tool. Adding a separate procedures directory just duplicates what skills already do, with no functional benefit. Simpler = better.

### Decision: Split /template into /template-create and /template-apply
**Why:** Two distinct operations with different inputs, outputs, and agent types. Splitting them means `/plan` can invoke just `/template-apply` without parsing mode flags. Cleaner cross-function interface.

### Decision: Extract /doc-update as its own skill
**Why:** Doc update logic is used by `/execute` (after each phase) and could escalate to `/analyze` (if changes are major). Making it a standalone skill means this orchestration lives in one place, not duplicated inside `/execute`.

### Decision: Main session as orchestrator
**Why:** The main session is the only context that can both invoke skills (Skill tool) and spawn agents (Agent tool) without restriction. Subagents can invoke skills but cannot spawn agents. This makes the main session the natural orchestrator — it follows skill instructions and dispatches work to agents.
