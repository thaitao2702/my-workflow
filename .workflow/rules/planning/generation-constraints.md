# Generation Constraints

Read this before writing `acceptance_criteria`, `test_requirements`, and `acceptance_specs`.

---

## Meta-Rule

**A valid requirement must be falsifiable by a plausible wrong implementation of THIS task.** If every implementation that compiles automatically passes it, the requirement adds nothing.

---

## Rejection Checklist

Before writing each criterion or test requirement, check these five questions. Reject if ANY answer is NO.

1. **Ownership** — Does it test THIS task's code? (not compiler, framework, library, or a future task)
2. **Falsifiable** — Can a plausible wrong implementation fail it? (not tautological, not true-by-definition)
3. **Concrete** — Can you name the input, action, and expected outcome? (not vague, not unbounded)
4. **Behavioral** — Does it test runtime behavior? (not code structure, not artifact existence)
5. **Non-redundant** — Does it verify something no other requirement in this task covers?

---

## Common Traps (reject on sight)

| Trap | Example | Why Invalid |
|------|---------|-------------|
| Compiler guarantee | "Verify abstract class can't be instantiated" | TypeScript enforces this at compile time |
| Tautology | "Verify enum has the specified values" | True by definition once written |
| Scope leak | "Verify concrete subclass implements all methods" | Subclass belongs to a different task |
| Vacuous | "Verify it works correctly" | No test predicate — what does "correctly" mean? |
| Zero-logic artifact | "Verify interface has correct properties" | Interfaces have no runtime behavior to test |
| Framework guarantee | "Verify lifecycle hooks fire in order" | Tests the framework, not your code |

---

## Task Descriptions

PROHIBITED in `tasks[].description`:
- Private implementation details (polling intervals, internal method bodies, algorithm choices, internal data structure layouts)
- Property paths (`config.auth.tokenExpiry`, `req.body.email`)
- CLI flags or command syntax (`--verbose`, `-p 3000`, `npm run build`)
- Package/library names as implementation directives ("use lodash.debounce", "with Express router")
- Code snippets, pseudocode, or implementation algorithms
- Line numbers or file byte offsets
- Inline signature definitions for cross-phase interfaces (use contract references instead)

PERMITTED — cross-phase contract references:
- "Receives BridgeHelper (Phase 3 contract-01) via constructor injection"
- "Calls the analysis service (Phase 2 contract-02) to process results"
These reference declared `interface_contracts[]` entries, not implementation details.

REQUIRED: behavioral requirements, constraints, boundaries, purpose, contract references for cross-phase dependencies.

---

## Acceptance Specs (additional rules)

- Derive from requirements, not from individual tasks
- `verify_by` describes a scenario ("do X, observe Y") — no framework syntax
- Every `scope.in_scope` requirement traces to at least one spec across all phases

---

## Parallel Safety

After writing all phase files, run two cross-checks:

**File cross-check:**
- Scan `tasks[].files` across phases in the same parallel group. If any file appears in two phases within the same group, move one phase to a later group.

**Interface dependency cross-check:**
- Scan `interface_contracts[].consumed_by_phases` across all phases. For each contract, verify that the defining phase is in an earlier execution group than every consuming phase. Phases with interface dependencies MUST NOT be in the same parallel group. If violated, move the consuming phase to a later group.

---

## Cross-Cutting

- **No contradictions** within a task's criteria/requirements set
- **No subsets** — if one requirement is strictly weaker than another, merge or remove
- **Scope boundary** — test what the artifact DOES, not how consumers will use it
