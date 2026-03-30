# Executor Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect all before constructing the prompt.

| Data | Source |
|------|--------|
| `$PLAN_DIR` | Resolved in Step 1a |
| Phase number | Current phase index |
| Mission briefing | `plan.json` → `summary` |
| Component intelligence | `plan.json` → `component_intelligence` |
| Risks & mitigations | `plan.json` → `risks` |
| Phase goal | `phase-{N}.json` → `goal` |
| Tasks | `phase-{N}.json` → `tasks` (descriptions, acceptance criteria, test requirements, file lists) |
| Resume point | `state current` output — omit if starting fresh |
| Project overview | `.workflow/project-overview.md` |
| Component analysis | Relevant `.analysis.md` files (Level 1: frontmatter + CONTENT) — guaranteed fresh by Step 2a analysis gate |
| Code quality rules | `.workflow/rules/code/*.md` (if any) |
| TDD policy | `.claude/rules/tdd-policy.md` |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions. Pass everything below this line as the subagent prompt.

**Plan Directory:** `{$PLAN_DIR}`
Use for all CLI state-tracking calls (`state set-active`, `complete-task`, etc.).

**Phase:** {phase_number}

**Mission Briefing:**
{mission_briefing}
Big-picture context — what we're building, why, and key constraints. Use this to guide implementation decisions when tasks are ambiguous.

**Component Intelligence:**
{component_intelligence}
Hidden constraints and non-obvious behaviors discovered during planning. Violations cause subtle bugs — respect these over your own assumptions.

**Risks & Mitigations:**
{risks}
Handle proactively. When you encounter a listed risk, apply its planned mitigation.

**Phase Goal:**
{phase_goal}
What this phase achieves and how it connects to other phases. Stay within this scope.

**Tasks:**
{tasks}
Implement in order. Each task's acceptance criteria are your definition of done, not suggestions.

**Resume Point:** *(include only if resuming)*
{resume_point}
Skip completed tasks. Start from the first incomplete task.

**Project Overview:**
{project_overview}
Codebase architecture, modules, and conventions. Match existing patterns.

**Component Analysis:**
{component_analysis}
API contracts, hidden behaviors, and integration patterns for components you'll modify. Check before assuming how an interface works.

**Code Quality Rules:**
{code_quality_rules}
Non-negotiable. All code must pass these standards.

**TDD Policy:**
{tdd_policy}
When to write tests first and when exceptions apply.

**Discoveries:**
After completing all tasks, end your output with a `## Discoveries` section. Report anything unexpected you found during implementation:
- Hidden behaviors not mentioned in the component analysis
- Wrong assumptions from the plan (constraints that didn't hold, APIs that worked differently)
- Edge cases you had to handle that weren't anticipated
- Integration gotchas future work should know about

If nothing unexpected was found, write `## Discoveries` followed by "None." Do NOT skip this section.
