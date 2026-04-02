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

Evaluate against all 7 dimensions:

1. **Acceptance criteria met** — every task's criteria verified
2. **Scope compliance** — no work outside scope boundaries
3. **Architectural alignment** — implementation matches plan summary constraints
4. **Risk mitigation** — identified risks adequately handled
5. **Test coverage** — every behavior has a corresponding test
6. **Code quality** — passes all loaded quality rules
7. **Convention compliance** — matches existing codebase patterns

## Output Format

Follow this format exactly:

```
## Status
**Result:** PASS | FAIL
**Passed:** {N}/{total}
**Failed Dimensions:** [{dimension names}]

## Dimensions
### {N}. {Dimension Name}
**Result:** PASS | FAIL
**Evidence:** {specific line/file reference from the diff}
**Fix Required:** {description of what needs fixing} | —

## Escalations
| Type | Dimension | Description |
|------|-----------|-------------|
| ambiguous_criteria ∣ conflicting_rules ∣ unclassifiable | {dimension name} | {details} |
```

- **Status.Result:** `PASS` = all 7 dimensions pass. `FAIL` = one or more dimensions fail.
- **Dimensions:** One subsection per dimension, in order. Every dimension must be evaluated — no skipping.
- **Fix Required:** Describe what needs fixing. Use "—" only if PASS.
- **Escalations:** Issues with the review criteria themselves, not with the code. Write "None" if no criteria issues.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: PASS ∣ FAIL | Decide: proceed or fix |
| | `**Passed**`: N/total | Quick severity gauge |
| | `**Failed Dimensions**`: list of names | Know which dimensions need fixes |
| `## Dimensions` | Per dimension: `**Result**`, `**Evidence**`, `**Fix Required**` | Specific fixes to apply if FAIL |
| `## Escalations` | Table: Type, Dimension, Description | Criteria issues to resolve before re-review. Type enum: `ambiguous_criteria`, `conflicting_rules`, `unclassifiable` |
