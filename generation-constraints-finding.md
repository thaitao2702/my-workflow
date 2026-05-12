# Finding: Generation Constraints Gap in Planning Pipeline

**Date:** 2026-04-09
**Triggered by:** Manual review of `phase-1.json` task-02 in plan `260408-qa-platform-e2e`
**Severity:** Structural — affects all plans generated without generation constraints

---

## 1. What Was Found

### The Specific Defect

In `phase-1.json`, task-02 ("Abstract test bridge base class") has this test requirement:

> "Verify a concrete subclass must implement all abstract methods"

This requirement is invalid for two independent reasons:

1. **Scope misalignment.** Task-02 creates the abstract base class `TestBridgeBase.ts`. The concrete subclass (`ZeusTestBridge.ts`) is task-03's deliverable. The test references an artifact that doesn't exist at the time task-02 completes.

2. **Compiler-testing.** TypeScript enforces `abstract` method implementation at compile time. If `ZeusTestBridge` omits an abstract method, `tsc` rejects the code. Writing a runtime test for this verifies the TypeScript compiler, not the project's code. No runtime test can meaningfully verify this — if the subclass compiles, it implements everything; if it doesn't, there's no code to test.

A similar issue exists with the first test requirement in the same task:

> "Verify the class cannot be instantiated directly (abstract)"

This also tests TypeScript's compile-time enforcement rather than runtime behavior of the code being written.

### What Should Have Been There Instead

Task-02 has concrete runtime behavior in the base class — the `EventCollector` integration and the `waitForState` polling helper. Valid test requirements would target these:

- EventCollector delegation: `startEvents()` / `stopEvents()` / `drainEvents()` correctly proxy to the internal EventCollector member
- Wait helper: polling resolves when condition is met, rejects on timeout (this was already the third requirement and is valid)

---

## 2. Root Cause Analysis

### Root Cause 1: `generation-constraints.md` Did Not Exist

The planning skill (`SKILL.md` Step 7) explicitly instructs:

> **Read `.workflow/rules/planning/generation-constraints.md` before writing steps 2-4.** Apply its rules while generating task descriptions, acceptance criteria, and acceptance specs. Violating them causes reviewer failures and wastes a full review round.

**The file did not exist.** The planner had zero explicit rules constraining what makes a valid `test_requirement` or `acceptance_criteria`. It generated them using only the vague guidance in SKILL.md ("verifiable by running something") — which the bad test requirements technically satisfy on a surface reading.

The architecture was designed for two layers of quality control (generation rules + reviewer enforcement), but the first layer was never populated.

### Root Cause 2: Reviewer Dimensions Were Shallow

The plan-reviewer evaluates 11 dimensions. The two relevant ones were:

| Dimension | Original Definition | Why It Missed the Bug |
|-----------|-------------------|----------------------|
| 7. Acceptance criteria completeness | "every task has verifiable criteria (not vague)" | The bad criteria aren't vague — they're precise but pointless. The dimension only checked presence and vagueness, not semantic validity. |
| 8. Test coverage mapping | "every behavior has a corresponding test requirement" | This maps behavior-to-test (coverage), but never asks whether the test requirement is within scope, tests the right thing, or is falsifiable. |

Neither dimension asked:
- "Does this test requirement test behavior of the code being written, or the language/compiler?"
- "Does this test requirement reference artifacts that exist within this task's scope?"
- "Can a plausible wrong implementation of this task cause this test to fail?"

---

## 3. Taxonomy of Invalid Requirements

The specific defect belongs to two broader classes. A full analysis identified **22 distinct classes** of semantically invalid test requirements and acceptance criteria, organized into 7 root-cause groups.

### Group A: Testing Things That Aren't The Task's Responsibility

The requirement verifies something owned by a different entity — the language, a framework, a dependency, or a different task.

#### Class 1: Language/Compiler Guarantee Testing

Asks to verify something the language's type system or compiler enforces statically. A runtime test is either impossible (won't compile) or tautological (if it compiles, it passes).

**Litmus test:** "Would this fail at compile time rather than runtime if violated?"

**Examples:**
- "Verify that the abstract class cannot be instantiated directly"
- "Verify that passing a string to a number parameter produces an error"
- "Verify that the readonly property cannot be reassigned"

#### Class 2: Framework/Runtime Guarantee Testing

Tests behavior guaranteed by the framework or runtime, not by the task's code.

**Litmus test:** "Is this testing the framework's behavior, or our code's use of the framework?"

**Examples:**
- "Verify that Cocos Creator lifecycle methods fire in order" (engine guarantee)
- "Verify that SignalR reconnects automatically" (library behavior)

#### Class 3: Scope Leakage (Cross-Task Testing)

Verifies behavior that belongs to a different task's scope. Creates phantom dependencies.

**Litmus test:** "Does the code that fulfills this requirement exist within THIS task's file/module scope?"

**Examples:**
- Task A creates abstract class; requirement says "verify concrete subclass implements all methods" (subclass is Task B)
- Task creates a data model; requirement says "verify the API endpoint returns this model" (endpoint is another task)

#### Class 4: Dependency Behavior Testing

Tests the behavior of an external dependency rather than the task's integration with it.

**Litmus test:** "If we replaced this dependency with a different one that has the same interface, would this test still be meaningful?"

**Examples:**
- "Verify that lodash.cloneDeep produces a deep copy"
- "Verify that WebSocket sends ping frames every 30 seconds"

---

### Group B: Testing Things That Can't Be Meaningfully Tested At This Level

The requirement is untestable, testable only at a different abstraction level, or requires infrastructure the task doesn't have.

#### Class 5: Non-Functional Without Measurement

States a quality attribute without specifying measurable thresholds.

**Litmus test:** "What specific number, condition, or observable behavior would make this test fail?"

**Examples:**
- "Verify the component renders efficiently"
- "Verify the function handles large datasets"

#### Class 6: Unbounded Negative-Space Testing

Asks to prove that something does NOT happen without bounding the search space.

**Litmus test:** "Can I enumerate the finite set of things to check for absence?"

**Examples:**
- "Verify the refactored code introduces no new bugs"
- "Verify the module has no side effects" (without enumerating which)

#### Class 7: Wrong-Level Testing

Asks for verification at a level where the behavior isn't observable.

**Litmus test:** "Can this behavior be observed at the test level specified for this task?"

**Examples:**
- Unit task for a calculation function: "Verify the value displays correctly in the UI"
- Integration task: "Verify the internal variable is set to null after cleanup"

#### Class 8: Implementation Prescription Disguised as Requirement

Dictates HOW something should be implemented rather than WHAT behavior it exhibits.

**Litmus test:** "Does this describe observable behavior, or code structure?"

**Examples:**
- "Verify the class uses the Singleton pattern" (valid: "all callers receive the same instance")
- "Verify the function uses recursion" (valid: "visits all nodes in depth-first order")

---

### Group C: Tautological, Vacuous, or Circular Requirements

The requirement is trivially true, says nothing falsifiable, or defines success in terms of itself.

#### Class 9: Tautological (True By Definition)

Restates what the code does by virtue of existing. If it compiles, it passes.

**Litmus test:** "Can I write code that satisfies the task description but FAILS this requirement?"

**Examples:**
- Task: "Create GameState enum." Requirement: "Verify GameState enum exists with specified values."
- Task: "Create ISpinResult interface." Requirement: "Verify interface defines correct properties."

#### Class 10: Vacuous (Says Nothing Falsifiable)

Sounds meaningful but has no testable predicate.

**Litmus test:** "What would the assert statement be?"

**Examples:**
- "Verify the code is well-structured"
- "Verify the function works as expected"

#### Class 11: Circular/Self-Referential

Defines acceptance in terms of itself.

**Litmus test:** "Does this reference something outside the task's own description as a source of truth?"

**Examples:**
- "Verify the function calculates the result correctly" (what is "correctly"?)
- "Verify the output matches the expected output" (what defines "expected"?)

---

### Group D: Temporal and Ordering Errors

References state, artifacts, or conditions that don't exist at the time the task executes.

#### Class 12: Premature Dependency Testing

Tests interaction with a component that hasn't been built yet.

**Litmus test:** "Do all components referenced in this requirement exist when this task completes?"

**Examples:**
- Task 1 creates a data model. Requirement: "Verify model serializes correctly via the API layer" (API layer is Task 5)

#### Class 13: Post-Hoc Verification

Can only be checked in an environment the task doesn't operate in.

**Litmus test:** "Can this be verified in an isolated test environment?"

**Examples:**
- "Verify the service handles 1000 concurrent users"
- "Verify the component renders correctly on iOS Safari"

---

### Group E: Misaligned Granularity and Redundancy

Wrong granularity level, duplicates other requirements, or tests intermediate steps.

#### Class 14: Over-Decomposed (Testing Intermediate Steps)

Tests internal implementation steps whose correctness is implied by end-to-end requirements.

**Litmus test:** "If I removed this, would remaining requirements still catch all real bugs?"

**Examples:**
- Separate requirements for "parses input", "validates parsed result", "transforms validated result" when one end-to-end test covers all three

#### Class 15: Duplicate/Overlapping

Two requirements test the same behavior in different words.

**Litmus test:** "Could a single test case satisfy both requirements?"

**Examples:**
- "Verify function returns null for invalid input" AND "Verify function handles invalid input gracefully"

#### Class 16: Zero-Logic Artifact Testing

Tests a purely declarative artifact with no conditional logic, branching, or computation.

**Litmus test:** "Does this artifact contain any conditional logic?"

**Examples:**
- "Verify PAYLINE_PATTERNS contains the correct 20 patterns" (static data)
- "Verify SpinResult interface has correct property types" (interfaces are erased at compile time)

#### Class 17: Missing Concrete Test Vectors

Describes a data transformation test without specifying which inputs and outputs.

**Litmus test:** "Are concrete input-output pairs specified?"

**Examples:**
- "Verify the payout calculator returns the correct payout" (for which inputs?)
- Valid: "Verify three ZEUS symbols on payline 1 with bet=10 returns payout=500"

---

### Group F: Semantic Contradictions and Impossibilities

Internally contradictory, logically impossible, or misunderstands the artifact's nature.

#### Class 18: Contradictory Requirements

Two requirements in the same task contradict each other.

**Litmus test:** "Can both be simultaneously true?"

**Examples:**
- "Verify function is pure (no side effects)" AND "Verify function logs a warning for invalid inputs"

#### Class 19: Category Error (Wrong Artifact Type)

Applies testing concepts appropriate for one artifact type to a fundamentally different one.

**Litmus test:** "Does this artifact type support the kind of verification being requested?"

**Examples:**
- "Verify the enum handles invalid inputs gracefully" (enums don't handle anything)
- "Verify the type alias performs the transformation correctly" (type aliases have no runtime behavior)

#### Class 20: Temporal Impossibility

Describes event sequences impossible in the system's execution model.

**Litmus test:** "Is the described sequence actually possible in this system?"

**Examples:**
- "Verify the synchronous function handles concurrent calls correctly" (single-threaded JS)

---

### Group G: Mismatched Verification Method

Implies a verification method that doesn't match the testing context.

#### Class 21: Visual/Subjective as Automated Test

Can only be verified by human inspection, but listed as an automated test requirement.

**Litmus test:** "Can a machine evaluate this to true/false without human judgment?"

**Examples:**
- "Verify the animation looks smooth"
- "Verify the error message is user-friendly"

#### Class 22: Code Review Criterion as Test

Describes a property of source code text rather than runtime behavior.

**Litmus test:** "Is this about what the code DOES when it runs, or what it LOOKS LIKE?"

**Examples:**
- "Verify all public methods have JSDoc comments"
- "Verify the function is no longer than 30 lines"

---

## 4. Unifying Principle

All 22 classes reduce to one meta-principle:

> **A valid test requirement must be falsifiable by code that satisfies the task description.**

That is — it must be possible to write a plausible implementation that completes the task but fails the requirement. If no such implementation exists (Classes 1, 9, 16), or the failure can't be detected at this level (Classes 5, 7, 13, 21), or the code that would fail it isn't in scope (Classes 3, 4, 12), the requirement is invalid.

---

## 5. What Was Fixed

### Layer 1: Generation Constraints (Planner-side prevention)

**Created:** `.workflow/rules/planning/generation-constraints.md`

The file the planner was already instructed to read but didn't exist. Contains principle-based litmus tests that the planner applies during Step 7 generation:

| Category | Litmus Tests |
|----------|-------------|
| **Acceptance Criteria** | 1. Ownership — criterion passes/fails based on THIS task's code? |
| | 2. Discrimination — plausible wrong implementation would fail it? |
| | 3. Objectivity — two people agree on PASS/FAIL without subjective judgment? |
| | 4. Behavioral Focus — describes runtime behavior, not code structure? |
| | 5. Logical Consistency — consistent with other criteria and execution model? |
| **Test Requirements** | 1. Attribution — failure indicates a bug in THIS task's code? |
| | 2. Falsifiability — plausible wrong implementation can cause failure? |
| | 3. Executability — runnable with artifacts available when task completes? |
| | 4. Concreteness — specifies scenario with inputs, actions, expected outcomes? |
| | 5. Behavioral Scope — verifies runtime behavior, not source-code properties? |
| | 6. Non-Redundancy — verifies behavior not covered by another requirement? |
| **Acceptance Specs** | Inherits criteria rules + Requirement Derivation, Integration Perspective, Framework Agnosticism |
| **Cross-Cutting** | Set-Level Consistency (no contradictions, no subsets), Scope Boundary Awareness (test own behavior, not consumers) |

### Layer 2: Reviewer Enforcement (Post-generation safety net)

**Updated:** `.claude/skills/plan/plan-reviewer-prompt.md` — dimensions 7 and 8

| Dimension | Before | After |
|-----------|--------|-------|
| **7** | "Acceptance criteria completeness — every task has verifiable criteria (not vague)" | "Acceptance criteria validity — every task has verifiable criteria (not vague), AND every criterion passes the generation constraint litmus tests. Flag: compiler guarantees, future-task dependencies, tautologies, structural-not-behavioral, subjective terms, contradictions" |
| **8** | "Test coverage mapping — every behavior has a corresponding test requirement" | "Test requirement validity — every behavior has a corresponding test requirement, AND every requirement passes the generation constraint litmus tests. Flag: language/compiler/framework testing, cross-task scope leaks, unfalsifiable tests, declarative artifact testing, vague predicates, implementation prescription, redundancy" |

### Defense-in-Depth Design

```
Plan Generation (Step 7)
  |
  |-- Planner reads generation-constraints.md
  |-- Applies litmus tests while writing criteria/requirements
  |-- Prevents most invalid items from being written
  |
  v
Plan Review (Step 8)
  |
  |-- Reviewer loads planning rules from .workflow/rules/planning/
  |-- Evaluates dimensions 7 & 8 with expanded flag criteria
  |-- Catches any invalid items that slipped through generation
  |
  v
User Review (Step 9)
  |
  |-- Final human check
```

---

## 6. Highest-Risk Classes for AI Planners

Based on how LLMs generate text, these classes are the most frequent offenders:

| Priority | Class | Why LLMs Fall Into It |
|----------|-------|----------------------|
| 1 | Class 9: Tautological | LLMs naturally restate task descriptions as verification criteria |
| 2 | Class 10: Vacuous | LLMs produce fluent-sounding but unfalsifiable language easily |
| 3 | Class 16: Zero-Logic Artifact | LLMs generate test requirements for every task regardless of artifact type |
| 4 | Class 3: Scope Leakage | LLMs reason about the full plan context and bleed future-task concerns into current-task requirements |
| 5 | Class 1: Compiler Guarantees | LLMs treat static and dynamic verification as interchangeable |

The generation constraints file prioritizes these through the Attribution and Falsifiability litmus tests, which are the strongest filters against the most common failure modes.
