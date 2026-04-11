# Planning Reference

Principles and constraints governing plan design (Steps 5-7). Loaded at Phase C entry.

---

## Planning Principles

### Phase Sizing
Each phase spawns one executor subagent that implements all tasks sequentially. All tasks in a phase must fit in one agent session. If the phase is too large, split into more phases — not more granular tasks.

### Task Granularity — The Coherent Unit
A task is the unit of progress tracking — the executor marks each task complete for resume. This means:

- **Lower bound:** A task must be a meaningful unit of progress worth tracking independently. A 2-line change doesn't need its own task. Merge trivially small changes (one import, one hook call, one type declaration) with related tasks.
- **Cohesion:** Tightly coupled changes belong in ONE task. If change A only makes sense because of change B, they're one task:
  - Type declaration + the class that uses it → one task
  - Public accessor + the code that calls it → one task
  - Two 1-line hooks in different files for the same concern → one task
- **The test:** Would a developer naturally do these changes in one sitting, one commit? If yes → one task.

**Bad granularity (9 tasks):**
- task-01: Create base class (1 file)
- task-02: Create type declaration (3 lines) ← too small, coupled with task-01
- task-05: Add accessor to CellView (2 lines)
- task-06: Use accessor in HoldSpinView (2 lines) ← coupled with task-05

**Good granularity (5 tasks, same work):**
- task-01: Create base class + type declaration (cohesive: type references the class)
- task-02: Implement bridge + activator (cohesive: activator instantiates bridge)
- task-03: CellView accessor + HoldSpinView wiring (cohesive: accessor exists for the wiring)

### Task Descriptions — WHAT and WHY, Never HOW (for internals)

Tasks describe **WHAT to build and WHY** — constraints, boundaries, purpose. The executor decides HOW for internal implementation by reading source code and analysis docs.

Exclude from descriptions: private method bodies, polling intervals, algorithm choices, internal data structure layouts, line numbers.

- **Good:** "Create abstract base class for test bridges. Must be pure TypeScript with zero engine imports."
- **Bad:** "Method waitForState: polls getAppState() every 200ms using setInterval, resolves when state matches, rejects after timeout." (leaks internal implementation)

**Exception — cross-phase dependencies:** When a task consumes a class or module produced by another phase, reference the interface contract by phase and ID: "Receives BridgeHelper (Phase 3 contract-01) via constructor injection." This is dependency coordination, not implementation leakage. See "Cross-Phase Interface Dependencies" principle below.

### Plan Summary as Mission Briefing
The `summary` field is the executor's primary orientation document. Every executor reads it before starting any task. It must answer: What are we building? Why? What are the key constraints and architectural decisions? What should the executor know that ISN'T in individual task descriptions?

Test: "If a new developer reads the summary + a task description, can they implement correctly?"

### Acceptance Criteria
Every criterion must be **verifiable by running something** — a test, a command, a query. "Works correctly" is NOT verifiable. "GET /api/reports returns 200 with JSON array matching ReportSchema" IS. If you can't write a verifiable criterion, the task isn't well-defined enough.

### Acceptance Specifications
Acceptance specifications (`acceptance_specs`) are **phase-level** verification targets consumed by an independent verifier after execution — distinct from task-level `acceptance_criteria`:

| Concept | Level | Consumer | Purpose |
|---------|-------|----------|---------|
| `acceptance_criteria` | Per-task | Executor | Definition-of-done during implementation |
| `acceptance_specs` | Per-phase | Acceptance verifier (post-execution) | Independent behavioral verification |

- Specs are derived from **requirements**, not from tasks — a spec may span multiple tasks via `traces_to`
- `verify_by` must be concrete enough for either a test author (write + run test code) or a reasoning agent (read code and trace behavior) to determine PASS/FAIL unambiguously
- Every requirement in `scope.in_scope` should trace to at least one `acceptance_spec` across all phases
- Specs verify **functional correctness** (does it work?), not code quality (that's the reviewer's job)

### Using Component Intelligence
Hidden details in analysis docs often reveal constraints that change the plan. If a component silently clamps date ranges to 90 days, your "export all data" feature needs pagination. Reference specific findings in `component_intelligence` so reviewers understand why you made certain choices.

### System Composition
Individual tasks pass review; the assembled system doesn't — this is the most expensive class of plan defect. Before writing tasks, trace the end-to-end flow from user action to system response:
- Every transition between phases needs a task that wires producer output to consumer input. If Phase A creates a service and Phase B creates an endpoint that calls it, something must connect them — don't assume it happens by itself.
- If no requirement explicitly states integration work (middleware, adapters, config, migrations) but the system needs it to function, add it as a task. The gap between requirements is where plans fail.
- When two phases produce/consume shared artifacts, their task descriptions must state compatible assumptions about the shared interface — even without specifying method signatures.

### Parallel Safety
Assign parallel groups (A, B, C...) to phases that can run simultaneously. **The #1 rule:** phases in the same group must NOT modify the same files — this prevents merge conflicts. When in doubt, put phases in separate groups. Sequential is safe; parallel is fast but risky.

### Cross-Phase Interface Dependencies

Each phase is implemented by an independent executor agent with no shared context. When Phase X's code imports or calls Phase Y's code, there is an interface dependency that must be declared in the plan and enforced through sequential execution.

**When dependencies must be declared:**
- Phase X's task says to "receive" or "use" an object created by Phase Y
- Phase X's task says to "call" a helper or service defined in Phase Y
- Phase X modifies a file originally created by Phase Y
- Two phases produce modules that a later phase integrates

**Sequential enforcement:** Phases with interface dependencies MUST be in different execution groups, with the producing phase in an earlier group than the consuming phase. This ensures the producing phase's code exists before the consuming phase starts, and enables the orchestrator to capture and forward the actual interface.

**What a dependency declaration contains (plan time):**
- Contract ID (unique within phase)
- Expected class or module name
- One-line purpose description
- Which task defines it
- Which phases consume it

**What it does NOT contain at plan time:** method signatures, parameter types, return types. These are determined by the executor during implementation and forwarded by the orchestrator to consuming phases.

**Where declarations live:** In the `interface_contracts` field of the phase that DEFINES the interface (the provider). The consuming phase's task description references the contract by phase number and contract ID.

**The rule of thumb:** Called only within the same phase → private, no declaration needed. Called from another phase → dependency, declaration required.

Good:
  Phase 3 declares BridgeHelper in interface_contracts with name, purpose, and
  consumed_by_phases: [2, 4]. Phase 3 is in Group A, Phase 2 is in Group B.
  Phase 2 task-02 says: "Receives BridgeHelper (Phase 3 contract-01) via
  constructor injection."

Bad:
  Phase 2 and Phase 3 are in the same parallel group. Phase 2 task-02 says:
  "Receives helper instances via constructor injection." Phase 3 task-01 says:
  "Implement bridge helper with async wrappers." Neither declares the dependency.
  Agents invent independently.

---

## Generation Constraints

Read this before writing `acceptance_criteria`, `test_requirements`, and `acceptance_specs`.

### Meta-Rule

**A valid requirement must be falsifiable by a plausible wrong implementation of THIS task.** If every implementation that compiles automatically passes it, the requirement adds nothing.

### Rejection Checklist

Before writing each criterion or test requirement, check these five questions. Reject if ANY answer is NO.

1. **Ownership** — Does it test THIS task's code? (not compiler, framework, library, or a future task)
2. **Falsifiable** — Can a plausible wrong implementation fail it? (not tautological, not true-by-definition)
3. **Concrete** — Can you name the input, action, and expected outcome? (not vague, not unbounded)
4. **Behavioral** — Does it test runtime behavior? (not code structure, not artifact existence)
5. **Non-redundant** — Does it verify something no other requirement in this task covers?

### Common Traps (reject on sight)

| Trap | Example | Why Invalid |
|------|---------|-------------|
| Compiler guarantee | "Verify abstract class can't be instantiated" | TypeScript enforces this at compile time |
| Tautology | "Verify enum has the specified values" | True by definition once written |
| Scope leak | "Verify concrete subclass implements all methods" | Subclass belongs to a different task |
| Vacuous | "Verify it works correctly" | No test predicate — what does "correctly" mean? |
| Zero-logic artifact | "Verify interface has correct properties" | Interfaces have no runtime behavior to test |
| Framework guarantee | "Verify lifecycle hooks fire in order" | Tests the framework, not your code |

### Task Descriptions

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

### Acceptance Specs (additional rules)

- Derive from requirements, not from individual tasks
- `verify_by` describes a scenario ("do X, observe Y") — no framework syntax
- Every `scope.in_scope` requirement traces to at least one spec across all phases

### Parallel Safety

After writing all phase files, run two cross-checks:

**File cross-check:**
- Scan `tasks[].files` across phases in the same parallel group. If any file appears in two phases within the same group, move one phase to a later group.

**Interface dependency cross-check:**
- Scan `interface_contracts[].consumed_by_phases` across all phases. For each contract, verify that the defining phase is in an earlier execution group than every consuming phase. Phases with interface dependencies MUST NOT be in the same parallel group. If violated, move the consuming phase to a later group.

### Cross-Cutting

- **No contradictions** within a task's criteria/requirements set
- **No subsets** — if one requirement is strictly weaker than another, merge or remove
- **Scope boundary** — test what the artifact DOES, not how consumers will use it
