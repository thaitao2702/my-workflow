# Reviewer Prompt Template

## For Orchestrator — Data to Collect

Each row names a data item and where to get it. Collect all before constructing the prompt.

| Data | Source |
|------|--------|
| Code changes | `git diff` for this phase |
| Mission briefing | `plan.json` → `summary` |
| Scope | `plan.json` → `scope` |
| Component intelligence | `plan.json` → `component_intelligence` |
| Risks & mitigations | `plan.json` → `risks` |
| Phase goal | `phase-{N}.json` → `goal` |
| Task acceptance criteria | `phase-{N}.json` → `tasks` |
| Component analysis | Relevant `.analysis.md` files |
| Code quality rules | `.workflow/rules/code/*.md` + `.claude/rules/quality-criteria.md` |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected data. Keep purpose descriptions and review dimensions. Pass everything below this line as the subagent prompt.

**Code Changes:**
{code_changes}
This is what you're reviewing. Every finding must reference specific lines from this diff.

**Mission Briefing:**
{mission_briefing}
What we're building and why. Use this to judge whether implementation decisions align with project goals.

**Scope:**
{scope}
What's in-scope and out-of-scope. Flag any work that falls outside these boundaries.

**Component Intelligence:**
{component_intelligence}
Hidden constraints the implementation must respect. Check whether the code violates any of these.

**Risks & Mitigations:**
{risks}
Were these risks adequately handled? Flag any that were ignored or incorrectly mitigated.

**Phase Goal:**
{phase_goal}
What this phase should achieve. Evaluate whether the implementation fulfills it.

**Task Acceptance Criteria:**
{task_acceptance_criteria}
Per-task verifiable conditions. Each must be satisfied — not aspirational, mandatory.

**Component Analysis:**
{component_analysis}
API contracts and hidden behaviors. Verify the implementation respects these interfaces.

**Code Quality Rules:**
{code_quality_rules}
Standards to enforce. Flag violations with specific line references.

## Review Dimensions

Evaluate against all 7 dimensions. For each, state PASS or FAIL with evidence:

1. **Acceptance criteria met** — every task's criteria verified
2. **Scope compliance** — no work outside scope boundaries
3. **Architectural alignment** — implementation matches plan summary constraints
4. **Risk mitigation** — identified risks adequately handled
5. **Test coverage** — every behavior has a corresponding test
6. **Code quality** — passes all loaded quality rules
7. **Convention compliance** — matches existing codebase patterns
