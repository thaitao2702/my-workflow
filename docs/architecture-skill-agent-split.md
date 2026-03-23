# Architecture Decision: Skill vs Agent Responsibility Split

## The Problem We Found

After implementing all skills and agents, we noticed a pattern: **skills and agents contained overlapping content.** Both described implementation steps, output formats, and quality rules. For example, the `/analyze` skill had a "Step 3: Analysis" section listing what the analyzer should identify (dependencies, patterns, hidden details), and the analyzer agent had a nearly identical "Full Mode: What to Do" section listing the same things.

This creates three problems:
1. **Duplication** — the same information lives in two places, doubling maintenance
2. **Drift risk** — when one gets updated, the other becomes stale
3. **Unclear ownership** — when the agent receives its task, does it follow the skill's instructions or its own? Which takes precedence?

## Research: How Other Frameworks Handle This

We analyzed four reference frameworks to understand how they split responsibilities:

### claude-config — "Script Dispatch" Model
- **Skills:** Minimal (15-35 lines). Just say "run this Python script, here are the parameters."
- **Agents:** Comprehensive (100-130 lines). Expert persona with decision rules, convention hierarchy, escalation criteria.
- **Pattern:** Skill dispatches, agent thinks.

### gsd — "Orchestration + Specialist" Model
- **Skills (Commands):** Orchestration entry points (30-50 lines). Parse input, spawn agent, verify output, route result.
- **Agents:** Full execution specialists (300-500+ lines). Include deviation handling, state management, authentication gates, verification protocols.
- **Pattern:** Skill routes, agent owns the entire execution domain.

### my-claude-setup — "Workflow Template + Domain Expert" Model
- **Skills:** Workflow templates (300-600 lines). Step-by-step process with what to read, what to check, output templates, task tracking.
- **Agents:** Domain specialists (150-250 lines). Tech stack expertise, codebase-specific patterns and anti-patterns, architecture knowledge.
- **Pattern:** Skill defines the workflow. Agent provides domain expertise.

### superpowers — "Complete Workflow + Simple Persona" Model
- **Skills:** Complete workflows (150-300 lines). Hard gates, checklists, process diagrams, integration orchestration, anti-patterns.
- **Agents:** Simple personas (50-100 lines). One job, 5-6 focus areas, structured output expectations.
- **Pattern:** Skill carries everything. Agent just needs to know its role.

### The Inverse Relationship

```
Skill Detail ←————————————————→ Agent Detail
    LOW                              HIGH
  claude-config                    claude-config
    (15 lines)                     (130 lines)

    HIGH                             LOW
  superpowers                      superpowers
   (300 lines)                      (50 lines)
```

When skills carry more orchestration, agents can be simpler. When skills just dispatch, agents need to carry everything. **There is no "right" answer — but the detail must live somewhere, and only once.**

## Our Constraints

Before deciding, we considered our specific architecture constraints:

1. **Skills run in the main session.** They can cross-call other skills (via Skill tool) and spawn agents (via Agent tool). Full orchestration capability.

2. **Agents run as subagents.** They can invoke skills (if Skill tool is in their tools list) but CANNOT spawn other agents. Limited orchestration.

3. **When a skill spawns an agent, the agent does NOT inherit the skill's content.** The agent only sees its own definition + whatever the orchestrator explicitly passes in the prompt.

4. **Skills define the workflow entry point.** Users invoke `/plan`, `/analyze`, etc. The skill is always the starting context.

Constraint #3 is critical: if the output format lives only in the skill, the orchestrator must copy it into the agent's prompt every time. If the output format lives in the agent, it's always available — but the skill can't verify against a format it doesn't know. **Solution: output format lives in the skill (which passes it to the agent and uses it for verification).**

## The Decision

### Skills Own: WHAT, WHERE, WHEN

| Responsibility | Why It Belongs in the Skill |
|---------------|---------------------------|
| **Input parsing** | The skill is the entry point — it receives user input first |
| **Orchestration flow** | Step sequencing, branching, decision points — the skill coordinates |
| **Cross-function calls** | Only the main session (running a skill) can invoke other skills |
| **What context to pass the agent** | The skill knows what files to read and what the agent needs |
| **Output format** | The skill defines the contract and verifies the result |
| **Verification steps** | The skill checks the agent's work before presenting to user |
| **User interaction** | The skill manages the conversation — when to ask, what to present |
| **File paths and naming rules** | Where output goes, how files are named |

### Agents Own: HOW to Think

| Responsibility | Why It Belongs in the Agent |
|---------------|---------------------------|
| **Role/persona** | "You are a component analysis specialist" — frames the agent's mindset |
| **Reasoning approach** | How to read code, what to look for, how to assess significance |
| **Decision framework** | When to decide autonomously vs escalate to the orchestrator |
| **Quality standards** | What "good" looks like — specificity, honesty, conciseness |
| **Anti-patterns** | Common mistakes to avoid — hallucination, over-generalization, scope creep |
| **Domain expertise** | Deep knowledge of the problem domain (analysis, planning, reviewing, etc.) |

### The Handoff

```
Skill says:                              Agent knows:
"Spawn the analyzer agent.               "I deeply read code to find
 Give it these source files.              hidden behaviors and patterns.
 Give it this project overview.           I think about how downstream
 Tell it mode=full.                       consumers would use this.
 Tell it to produce output in             I never hallucinate — if unsure,
 this format: [format].                   I re-read the code.
 Write to this path."                     I'm specific, not generic."
     │                                         │
     └────────── Agent prompt combines both ───┘
```

The skill controls the **task assignment**. The agent controls the **thinking approach**.

## What Changed: Before and After

### Analyzer Agent

**Before (69 lines):**
```markdown
## Full Mode: What to Do
1. Read all source files thoroughly
2. Read test files
3. Cross-reference dependencies
4. Identify:
   - Component name and type
   - All dependencies with purpose and key interfaces
   - Public API / props / exports with types
   ...
5. Write the .analysis.md at the specified output path

## Quality Rules
- Be specific, not generic.
- Hidden Details table is the highest-value section.
- Diagrams are mandatory.
- Don't hallucinate.
- Stay under ~800 tokens total.
```

Problem: This is a recipe ("do step 1, then step 2"). It duplicates the skill's step list and includes format/constraint details that belong in the skill.

**After (60 lines):**
```markdown
## How You Think

### Reading Code
- Read every function, not just exports. Internal helpers
  often contain hidden business logic.
- Read test files to understand intended vs actual behavior.
- Cross-reference dependency docs when provided.

### Identifying What Matters
- Public API is the contract — document every prop, parameter.
- Integration patterns should be real code, not pseudocode.
- Hidden details are the highest-value output. These are things
  that would surprise someone who only read the public API.

### Specificity Over Generality
- Bad: "Handles data loading"
- Good: "Fetches paginated report data via SWR with 30s
  revalidation, transforms API response into ChartData format"

## Decision Framework

### When to escalate
- Component violates its stated purpose
- Component has no tests and complex logic

### When to decide autonomously
- Which patterns are being used
- What the hidden details are
- How to write the diagrams
```

Difference: The agent now describes **how to think about analysis** — reading strategies, what matters, specificity standards, escalation rules. The step-by-step recipe and output format stay in the skill.

### Planner Agent

**Before (55 lines):**
```markdown
## Planning Rules

### Task Design
- Each task must be completable in one agent session
- Tasks describe WHAT and WHY, not HOW
- Every task must have verifiable acceptance criteria

### File Scope Safety
- List all files each task will create or modify
- Cross-check: parallel phases can't touch the same file

## Output Format
Follow the exact formats specified by the orchestrator.

## Constraints
- Do NOT include implementation code
- Do NOT exceed 5 phases
```

Problem: Rules and constraints are useful but presented as a checklist. No guidance on *how to think about decomposition*.

**After (58 lines):**
```markdown
## How You Think

### Decomposition
- Break work into phases that follow natural dependency order.
- Each phase should be independently testable.
- Each task should be completable in one agent session.
  If unsure, split it. Too small is annoying; too large is dangerous.

### Task Descriptions
- Tasks describe WHAT and WHY, never HOW.
- "Add a status field to the reports table" — good.
- "Run ALTER TABLE..." — bad. You're making implementation
  decisions that belong to the executor.

### Using Component Intelligence
- Read the .analysis.md docs. Hidden details often reveal
  constraints that change the plan.
- Reference specific findings in your Component Intelligence
  section so reviewers understand your choices.

### Parallel Safety
- The #1 rule: phases in the same group must NOT modify
  the same files. When in doubt, put in separate groups.

## Decision Framework

### Decide autonomously
- Phase ordering and grouping
- Task granularity
- Risk assessment

### Escalate to user
- Scope ambiguity
- Conflicting requirements
- Architecture decisions with multiple valid approaches
```

Difference: Same rules, but framed as thinking approaches with reasoning. The agent now understands *why* tasks describe WHAT not HOW, *why* parallel safety matters, and *when* to make decisions vs ask.

### Reviewer Agent

**Before (78 lines):**
```markdown
## Plan Review: 8 Dimensions
### 1. Requirement Coverage
- Every requirement maps to at least one task
- FAIL if: any requirement has no corresponding task

### 2. Task Atomicity
...

## Code Review
1. Read all project-specific code rules
2. Review against ALL rules
3. Check: do changes match acceptance criteria?

## Output Format
```markdown
## Review Report
### Summary
{PASS | FAIL}
### Findings
#### Dimension 1: ... — PASS
```
```

Problem: The 8 dimensions are repeated from the skill (which also lists them). The output format belongs in the skill. The agent should know how to think about reviewing, not just what to check.

**After (48 lines):**
```markdown
## How You Think

### Reviewing Plans
- Check structural quality: is this buildable?
- Check completeness: does every requirement have a task?
- Check safety: can parallel phases conflict?
- You enforce the dimensions given by the orchestrator.
  Don't invent your own criteria.

### Severity Assessment
- FAIL if there's a concrete problem with evidence.
- PASS only if you checked and found no issues.
- When in doubt, fail. Catching false positives is cheap.
  Missing real problems is expensive.

## Decision Framework

### Decide autonomously
- Pass/fail on each dimension
- Severity of findings

### Escalate
- Ambiguity in the criteria themselves
- Conflicting rules
```

Difference: The 8 dimensions list stays in the skill (where it defines the contract). The agent now knows *how to assess severity*, *when to fail vs pass*, and *what attitude to bring to reviewing*. The output format moved to the skill.

### Executor Agent

**Before (52 lines):**
```markdown
## Execution Order
### 1. Understand Context
- Read task description and acceptance criteria
- Read relevant .analysis.md docs

### 2. Write Tests First (TDD)
- Write test(s) that verify each acceptance criterion
- Run tests — confirm they FAIL

### 3. Implement
- Write minimum code to pass all tests
- Run type checker if applicable

### 4. Verify
- All acceptance criteria met
- All tests pass

## Quality Rules
- Use strongest type system available
- Never swallow errors silently
...

## Output
Report back: Status, Files changed, Tests, Notes
```

Problem: Step-by-step recipe that duplicates the skill's description of what the executor does. Quality rules duplicate `.claude/rules/quality-criteria.md`.

**After (48 lines):**
```markdown
## How You Think

### Understanding Before Coding
- Read task description completely before writing code.
- Read .analysis.md docs — they reveal hidden behaviors
  you'd otherwise discover the hard way.
- Read actual source files. Understand existing patterns
  before adding to them.

### TDD Discipline
- Write test first, run it, watch it fail for the expected
  reason. If it passes, the criterion is already satisfied.
- Implement minimum code to pass. Don't add unasked features.
- TDD exceptions exist — document why you skipped, then implement.

### Following Conventions
- Match existing patterns. If services use repository pattern,
  yours should too.
- If existing pattern seems wrong, implement using it anyway
  and note the concern. Don't unilaterally refactor.

## Decision Framework

### Decide autonomously
- Implementation approach (plan says WHAT, you decide HOW)
- Test framework choice (follow project convention)

### Escalate
- Task description is ambiguous
- Existing code has a bug that blocks your task
- Task scope seems wrong
```

Difference: Same TDD discipline, but framed as a thinking approach. Removed duplicated quality rules (already loaded via `.claude/rules/`). Added the important "follow conventions even if they seem wrong" guidance.

### Doc-Updater Agent

**Before (53 lines):** Listed classification examples, patching steps, report format.

**After (49 lines):** Describes the *judgment* of classification — how to distinguish NO/MINOR/MAJOR, the principle "when in doubt choose MAJOR," and surgical patching philosophy.

### Template Extractor Agent

**Before (49 lines):** Listed analysis steps, output format, variable extraction steps.

**After (58 lines):** Describes how to *see patterns* (look past specific implementation to the shape), how to *honestly classify variability* (resist marking everything [P]), and why gotchas always exist.

### Template Applier Agent

**Before (44 lines):** Mapping table, output format, substitution rules.

**After (45 lines):** How to translate steps to tasks, preserve context, and choose granularity. Output format moved to skill.

## Skills: What Changed

Skills were already mostly well-structured as orchestration. Minor adjustments:

| Skill | Change |
|-------|--------|
| `/analyze` | Removed "Constraints" section that duplicated agent quality rules. Kept output format, added "pass this format to the agent" instruction. |
| `/plan` | No changes needed — already clean orchestration. The 8 review dimensions are the contract (what to check), not the approach (how to review). |
| `/execute` | No changes to agent delegation. Error handling section added (Phase 7 work, separate from this refactor). |
| `/doc-update` | No changes needed — already clean. Classification table describes expected output, not how to think. |
| `/template-create` | No changes needed — lists what the agent produces (output contract), not how to think about extraction. |
| `/template-apply` | No changes needed. |
| `/init` | No changes needed — `/init` doesn't spawn a named agent, it runs analysis directly in main session. |

## Summary: The Split Rule

```
┌─────────────────────────────────────────────────┐
│                    SKILL                         │
│                                                  │
│  "Parse the user's input.                        │
│   Check for staleness.                           │
│   If stale, spawn the analyzer agent.            │
│   Give it these files, this format.              │
│   Verify the output has correct frontmatter.     │
│   Report to the user."                           │
│                                                  │
│  Owns: Input, Flow, Context, Format, Verify, UX  │
└──────────────────────┬──────────────────────────┘
                       │ spawns with task + format
                       ▼
┌─────────────────────────────────────────────────┐
│                    AGENT                         │
│                                                  │
│  "I'm a component analysis specialist.           │
│   I read every function, not just exports.       │
│   Hidden details are my highest-value output.    │
│   I'm specific, not generic.                     │
│   I never hallucinate.                           │
│   When unsure, I re-read the code."              │
│                                                  │
│  Owns: Thinking, Judgment, Expertise, Standards  │
└─────────────────────────────────────────────────┘
```

**One sentence:** The skill is the manager (assigns work, defines deliverables, checks results). The agent is the specialist (knows the domain, brings expertise, makes quality judgments).
