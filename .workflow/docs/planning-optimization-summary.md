# Planning Process Optimization — Summary

**Date:** 2026-04-08
**Trigger:** `/plan` skill taking 40-45 minutes for large plans (8 phases, 22 tasks), expected 15-20 minutes.
**Source analysis:** `.workflow/plans/260407-qa-platform-framework/planning-process-report.md`

---

## Root Cause Analysis

72% of total time was in Phase D (Quality Review). Breakdown:

| Cause | Time Lost | Category |
|-------|----------|----------|
| Reviewer agent I/O-bound: 88 tool calls, ~11 sec each | ~9 min | Architecture — sequential CLI + file reads |
| Background agent stall → redundant second reviewer | ~8 min | Operational — no foreground guidance |
| Initial plan draft had 5 predictable defects → mandatory revision round | ~10-17 min | Quality gap — abstract principles, not concrete rules |
| Review round 2 re-reads everything from scratch | ~5 min | Architecture — no data caching between rounds |

---

## Decisions Made

| # | Decision | Reasoning | Status |
|---|----------|-----------|--------|
| 1 | **Prevent defects during planning, not detect after** | User insight: post-planning self-check is just a second review. Bake concrete rules into planning step instructions so defects never get written. | Pending implementation |
| 2 | **Single reviewer, not parallel per-phase** | 5/11 review dimensions require cross-phase analysis. Per-phase parallel reviewers can't evaluate dependency correctness, file scope safety, consistency, requirement coverage, or spec coverage. Architecture B (hybrid) adds coordination complexity without clear payoff. | Decided — keep single reviewer |
| 3 | **AI-friendly data dump over batch CLI commands** | Instead of many small CLI calls, one `review-dump` returns all plan data + cross-reference tables. Eliminates ~50 tool calls per review round. | Implemented |
| 4 | **Generic `batch` command over per-operation batch** | User insight: don't invent combined syntax per operation. Accept JSON array of independent sub-commands, execute sequentially, return sectioned output. Works for any mix of `read`, `grep`, `analysis`, `plan` commands. | Implemented |
| 5 | **CLI does data, reviewer does judgment** | Cross-reference tables are pre-computed data (file ownership map, requirement traces, spec traces) but no `⚠` markers — review logic stays in the reviewer agent only. | Implemented |
| 6 | **Run reviewer in foreground by default** | No parallel work during review = no reason for background. Foreground gives progress visibility, prevents redundant launches. | Implemented |
| 7 | **Drop incremental review (round 2+)** | Regression risk too high. A fix to one dimension can silently break another. Full re-review is safer. | Decided — dropped |
| 8 | **Drop split reviewer into two passes** | User rejected. Single reviewer with better data loading is simpler. | Decided — dropped |

---

## What Was Implemented

### CLI Changes (`workflow_cli.py`)

| Command | Purpose |
|---------|---------|
| `batch --commands 'JSON_ARRAY'` | Execute N sub-commands in 1 call, sectioned output |
| `read FILE [FILE:start-end ...]` | Read multiple files in 1 call |
| `grep [--path P] [--type T] [--context N] PATTERN` | Regex search wrapping ripgrep |
| `plan review-dump --plan-dir DIR` | All plan data + cross-reference tables + planning rules in AI-friendly text format |

Architecture: Refactored all command functions to raise `CLIError` instead of `sys.exit()`. Added `dispatch()` function for programmatic invocation with captured stdout.

### Instruction Updates (13 files)

| File | Change |
|------|--------|
| `rules/agent-contracts.md` | New "Batch Command Usage (All Agents)" universal section |
| `scripts/workflow_cli.reference.md` | Documented all new commands |
| `skills/plan/plan-reviewer-prompt.md` | Sequential CLI → `review-dump` + `batch` two-step loading |
| `agents/plan-reviewer.md` | "Reading Plans" uses `review-dump`, "Stale Data Review" anti-pattern updated |
| `skills/plan/SKILL.md` | Step 8: foreground directive for reviewer spawning |
| `agents/executor.md` | SOP step 1: batch-load source + analysis docs. Step 2b: reference batch context |
| `skills/execute/reviewer-prompt.md` | Orchestrator batch collection tip |
| `skills/execute/acceptance-verifier-prompt.md` | Orchestrator tip + reason mode batch-load |
| `skills/analyze/analyzer-prompt.md` | Orchestrator tip for tree mode |
| `agents/analyzer.md` | Tree mode: batch-load upfront, reference from context in loop |
| `skills/doc-update/doc-updater-prompt.md` | Orchestrator tip + batch hash computation |
| `skills/template-create/template-extractor-prompt.md` | A-disk mode → `review-dump` + batch tip |

### Expected Impact

| Metric | Before | After |
|--------|--------|-------|
| Reviewer tool calls per round | ~88 | ~35-40 |
| Data loading calls | ~50 | ~2 (review-dump + batch) |
| Time per review round | 10-17 min | ~5-8 min |
| Redundant reviewer launches | Possible | Prevented (foreground) |
| System-wide agent I/O (all agents) | N sequential calls | 1 batch call per context-load |

---

## What's Left

### P1: Strengthen Planning Rules as Prevention

**Status:** Implemented (2026-04-08).

**Problem:** The SKILL.md had abstract principles ("WHAT and WHY, Never HOW") but the planner still produced defects that the reviewer catches:
1. Implementation leakage in task descriptions (method names, CLI flags, package names)
2. External doc references in acceptance criteria ("spec Section 4.1")
3. Missing acceptance specs for tasks
4. Vague/unverifiable acceptance criteria

**Solution implemented:** Added "Generation Constraints" block inside Step 7 of SKILL.md with concrete PROHIBITED content lists for task descriptions, acceptance criteria, and acceptance specs. Added forward reference in Step 5 so constraints are visible during direction design. Rules are at the point of generation — not a post-check.

Constraints cover:
- Task descriptions: no method/function/class names, property paths, CLI flags, package names, code snippets, line numbers
- Acceptance criteria: no external doc references, no subjective language, must pass "I can verify by running ___" test
- Acceptance specs: every `scope.in_scope` must have coverage, `verify_by` must be framework-agnostic and unambiguous
- Parallel safety: file cross-check across same-group phases

**Expected impact:** Eliminates most first-round reviewer failures → eliminates one full review round (5-17 min saved).

**Combined expected result (all optimizations):** Large plans (8+ phases) should take 15-20 minutes instead of 40-45 minutes.
