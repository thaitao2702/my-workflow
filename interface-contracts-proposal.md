# Interface Contracts at Phase Boundaries — Proposal (v2)

**Target files:**

| File | Changes |
|------|---------|
| `.claude/skills/plan/SKILL.md` | #1, #2, #3, #4, #5, #6 |
| `.claude/skills/plan/plan-reviewer-prompt.md` | #7, #8 |
| `.workflow/rules/planning/generation-constraints.md` | #9 |
| `.claude/skills/execute/executor-prompt.md` | #10, #11 |
| `.claude/skills/execute/SKILL.md` | #12 |

**Status:** Proposal — awaiting review and integration
**Scope:** 12 changes across 5 files

---

## Problem Statement

The plan skill produces phased execution plans where each phase is implemented by an independent executor agent. These agents have no shared context — they only see their own phase's task descriptions, the mission briefing, and component intelligence.

When Phase X's code must import or call Phase Y's code (e.g., `step_executor.py` calls `bridge.trigger_action()`), both agents need to agree on:

- Class names
- Public method names
- Parameter names and types
- Return types

Currently, nothing in the planning pipeline ensures this agreement. Independent agents invent incompatible function signatures, causing integration failures that only surface during integration testing — after all phases have been implemented.

---

## Root Cause Chain

The problem originates in the "WHAT and WHY, Never HOW" planning principle, which treats all method signatures as implementation leakage. This correct principle is applied without distinguishing between two fundamentally different categories:

- **Private internals** — implementation details that belong to the executor
- **Public cross-phase interfaces** — coordination contracts that belong to the plan

This category confusion cascades through the system in a self-reinforcing loop:

| Node | Effect |
|------|--------|
| Planning principle | Does not distinguish private internals from public cross-phase interfaces |
| `tasks[].description` field definition | Explicitly excludes method signatures — planner cannot put contracts in tasks |
| Phase JSON format | No field exists for interface contracts — nowhere to declare cross-phase dependencies |
| Reviewer Dimension 4 | Flags method signatures in descriptions as violations — reviewer rejects valid contract references |
| Parallel Safety principle | Checks file-level conflicts only, not code-level interface dependencies — allows parallel execution of coupled phases |
| Step 7 (Write Plan Files) | No step identifies cross-phase code boundaries or triggers dependency analysis |
| Anti-pattern watchlist | No pattern defined for undefined cross-phase interfaces |
| Executor output format | No section for reporting public interfaces — orchestrator cannot capture what was built |
| Execute skill | No protocol for forwarding interfaces from a producing phase to consuming phases |

Each node reinforces the problem. Fixing only one leaves the others blocking it.

---

## Design Decisions

Three architectural decisions shape this proposal:

### Decision 1: Sequential execution for interface-coupled phases

Phases with cross-phase code dependencies (one imports/calls the other) MUST run sequentially. No parallel execution for coupled phases.

**Why:** Parallel execution of coupled phases is the hardest version of the problem — neither agent can see the other's output. Sequential execution eliminates this entirely: by the time the consuming phase starts, the producing phase's code exists on disk. The orchestrator can capture the actual interface and pass it forward.

**Trade-off:** Some plans lose parallelism. Correctness over speed.

### Decision 2: Flow-forward model — signatures from execution, not planning

The planner does NOT write function signatures. It declares that a dependency exists (which phases, what purpose). Actual signatures emerge during execution:

1. **Plan time:** Planner declares dependency — class name, purpose, which phases consume it
2. **Execution time:** Producing phase's executor implements the code and self-reports its public interface
3. **Forwarding:** Orchestrator captures the reported interface and injects it into the consuming phase's executor prompt

**Why:** The planner predicts; the executor knows. Signatures from implemented code are correct by construction. Signatures from planning are guesses that may need modification — creating a modification protocol problem that doesn't need to exist.

### Decision 3: Deterministic executor output format

The executor's interface self-report follows a fixed, parseable format. LLMs produce structured output reliably when given an exact template.

---

## Concrete Example

From the `qa-platform-framework` plan, Phase 2 (Core Framework) and Phase 3 (Helpers):

- Phase 2's `step_executor.py`: "Receives helper instances (bridge, gemini, artifact, network) via constructor injection"
- Phase 3's `bridge.py`: "Async Playwright-side wrappers for game bridge API"

**Current behavior (broken):**

Neither side specifies class names, method names, or signatures. Phases run in parallel. Two agents invent incompatible interfaces. Integration fails.

**Proposed behavior:**

1. Planner declares dependency: Phase 2 consumes `BridgeHelper` from Phase 3
2. Planner enforces sequential ordering: Phase 3 runs before Phase 2 (or in an earlier group)
3. Phase 3 executor implements `BridgeHelper`, self-reports the public interface:
   ```
   ### contract-01: BridgeHelper
   **File:** src/helpers/bridge.py
   **Signature:**
   ```python
   class BridgeHelper:
       def __init__(self, page: Page)
       async def trigger_action(self, name: str, params: dict | None = None) -> Any
       async def drain_events(self) -> list[dict]
       async def wait_for_state(self, state: str, timeout_ms: int = 10000) -> None
       async def start_event_collection(self) -> None
       async def stop_event_collection(self) -> None
   ```
4. Orchestrator captures this and injects it into Phase 2's executor prompt
5. Phase 2 executor sees the actual interface — no guessing

---

## Proposed Changes

### Change 1 — Refine "WHAT and WHY, Never HOW" Principle

**Location:** `SKILL.md` → Planning Principles → "Task Descriptions — WHAT and WHY, Never HOW"

**Current text:**

```
#### Task Descriptions — WHAT and WHY, Never HOW
Tasks describe WHAT to build and WHY — constraints, boundaries, purpose. The executor
decides HOW by reading source code and analysis docs.

- Good: "Create abstract base class for test bridges. Must be pure TypeScript with zero
  engine imports. Methods: register, waitForState (polling-based), getSnapshot."
- Bad: "Create TestBridgeBase.ts. Method waitForState: polls getAppState() every 200ms
  using setInterval, resolves when state matches, rejects after timeout."

The bad example leaks implementation (polling interval, exact property paths) into
the plan. The executor discovers these by reading source code — pre-deciding means
the planner guesses and the executor follows blindly.
```

**Proposed replacement:**

```
#### Task Descriptions — WHAT and WHY, Never HOW (for internals)

Tasks describe WHAT to build and WHY — constraints, boundaries, purpose. The executor
decides HOW for internal implementation by reading source code and analysis docs.

Exclude from descriptions: private method bodies, polling intervals, algorithm choices,
internal data structure layouts, line numbers.

- **Good:** "Create abstract base class for test bridges. Must be pure TypeScript with
  zero engine imports."
- **Bad:** "Method waitForState: polls getAppState() every 200ms using setInterval,
  resolves when state matches, rejects after timeout." (leaks internal implementation)

**Exception — cross-phase dependencies:** When a task consumes a class or module
produced by another phase, reference the interface contract by phase and ID:
"Receives BridgeHelper (Phase 3 contract-01) via constructor injection."
This is dependency coordination, not implementation leakage. See "Cross-Phase Interface
Dependencies" principle below.
```

---

### Change 2 — New Planning Principle: "Cross-Phase Interface Dependencies"

**Location:** `SKILL.md` → Planning Principles → new section after "Parallel Safety"

**Proposed content:**

```
#### Cross-Phase Interface Dependencies

Each phase is implemented by an independent executor agent with no shared context.
When Phase X's code imports or calls Phase Y's code, there is an interface dependency
that must be declared in the plan and enforced through sequential execution.

**When dependencies must be declared:**
- Phase X's task says to "receive" or "use" an object created by Phase Y
- Phase X's task says to "call" a helper or service defined in Phase Y
- Phase X modifies a file originally created by Phase Y
- Two phases produce modules that a later phase integrates

**Sequential enforcement:** Phases with interface dependencies MUST be in different
execution groups, with the producing phase in an earlier group than the consuming
phase. This ensures the producing phase's code exists before the consuming phase
starts, and enables the orchestrator to capture and forward the actual interface.

**What a dependency declaration contains (plan time):**
- Contract ID (unique within phase)
- Expected class or module name
- One-line purpose description
- Which task defines it
- Which phases consume it

**What it does NOT contain at plan time:** method signatures, parameter types, return
types. These are determined by the executor during implementation and forwarded by the
orchestrator to consuming phases.

**Where declarations live:** In the `interface_contracts` field of the phase that
DEFINES the interface (the provider). The consuming phase's task description references
the contract by phase number and contract ID.

**The rule of thumb:** Called only within the same phase → private, no declaration
needed. Called from another phase → dependency, declaration required.

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
```

---

### Change 3 — Phase JSON Format: Add `interface_contracts` Field

**Location:** `SKILL.md` → Phase File Format: `phase-{N}.json` — add after `acceptance_specs`

**Proposed addition to the JSON schema example:**

```json
{
  "interface_contracts": [
    {
      "id": "contract-01",
      "name": "BridgeHelper",
      "description": "Playwright-side wrapper for game test bridge API",
      "defined_in_task": "task-01",
      "consumed_by_phases": [2, 4]
    }
  ]
}
```

**Field definitions to add:**

```
interface_contracts[]
  Required only when this phase produces public APIs consumed by other phases.
  Omit entirely if the phase has no cross-phase consumers.
  Signatures are NOT included at plan time — they are captured from executor
  output during execution and forwarded by the orchestrator.

interface_contracts[].id
  Unique within the phase. Format: contract-NN (e.g., contract-01, contract-02).

interface_contracts[].name
  Expected class or module name. A planning-level coordination name — the
  executor should use this name unless there is a strong reason to deviate.

interface_contracts[].description
  One-line purpose description.

interface_contracts[].defined_in_task
  The task ID within this phase that creates this class or module.

interface_contracts[].consumed_by_phases
  Array of phase numbers that import or call this interface.
  Used by the reviewer to verify sequential ordering and cross-references.
```

---

### Change 4 — Update `tasks[].description` Field Definition

**Location:** `SKILL.md` → Phase File Format field definitions → `tasks[].description`

**Current:**

```
tasks[].description: WHAT and WHY, never HOW — see "Task Descriptions" principle above.
Exclude: property paths, method signatures, implementation code, line numbers.
```

**Proposed:**

```
tasks[].description: WHAT and WHY, never HOW for internal implementation — see "Task
Descriptions" principle above. Exclude: private method bodies, polling intervals,
algorithm choices, line numbers.

When the task consumes a cross-phase service, reference the interface contract:
"Receives BridgeHelper (Phase 3 contract-01) via constructor injection."
Do not re-define signatures inline — reference the contract by phase and ID.
```

---

### Change 5 — New Anti-Pattern: "Undefined Cross-Phase Interface"

**Location:** `SKILL.md` → Anti-Pattern Watchlist → new entry

**Proposed content:**

```
### Undefined Cross-Phase Interface

**Detection:** Phase X's task says "calls the bridge helper" or "receives helpers via
injection" but neither Phase X nor the defining phase declares the dependency in
`interface_contracts`. Two independent executor agents will have no coordination,
and the consuming agent won't receive the producing agent's interface.

**Resolution:** Identify every cross-phase code dependency — any place where Phase X's
code imports or calls Phase Y's code. For each:
1. Add an `interface_contracts` entry on the defining phase (the provider)
   with contract ID, expected class name, purpose, and consumed_by_phases.
2. Ensure the producing phase is in an earlier execution group than all
   consuming phases (sequential enforcement).
3. In the consuming phase's task description, reference the contract:
   "Receives BridgeHelper (Phase 3 contract-01)."

Private and internal functions within a single phase do not need declarations —
they are the executor's domain.
```

---

### Change 6 — New Sub-Step in Step 7: Identify Cross-Phase Dependencies

**Location:** `SKILL.md` → Step 7: Write Plan Files → new sub-step after current sub-step 4 (write acceptance specs)

**Proposed content:**

```
5. **Identify and declare cross-phase dependencies:** Scan all phases for cross-phase
   code dependencies — any place where Phase X's code imports, calls, or receives
   objects created by Phase Y.

   For each dependency:
   a. Identify the **defining phase** (the one that creates the class or module)
   b. Add an `interface_contracts` entry to that phase's JSON: contract ID, expected
      class name, purpose description, defined_in_task, consumed_by_phases
   c. In the **consuming phase's** task description, add a contract reference:
      "Receives BridgeHelper (Phase 3 contract-01) via constructor injection"
   d. **Enforce sequential ordering:** verify that the defining phase is in an earlier
      execution group than ALL consuming phases listed in consumed_by_phases.
      If not, move the consuming phase to a later group.

   Only cross-phase interfaces need declarations — internal functions within a single
   phase are the executor's domain.
```

Renumber the current sub-step 5 to sub-step 6.

---

### Change 7 — Update Plan-Reviewer Dimension 4

**Location:** `plan-reviewer-prompt.md` → Review Dimensions → Dimension 4

**Current:**

```
4. Task description quality — descriptions say WHAT/WHY, not HOW. Flag: exact property
   paths, method signatures, implementation code, line numbers in descriptions
```

**Proposed:**

```
4. Task description quality — descriptions say WHAT/WHY, not HOW for internal
   implementation. Flag: private implementation details (polling intervals, internal
   method bodies, algorithm choices, line numbers). Do NOT flag references to interface
   contracts declared in interface_contracts[] — these are cross-phase dependency
   coordination, not implementation leakage. Flag descriptions that define signatures
   inline instead of referencing the contract by phase and ID.
```

---

### Change 8 — New Reviewer Dimension: Interface Dependency Coverage

**Location:** `plan-reviewer-prompt.md` → Review Dimensions → add as new Dimension 12

**Proposed content:**

```
12. Interface dependency coverage — when Phase X's task describes calling, receiving, or
    importing code from Phase Y, verify:
    (a) The defining phase (Y) has an interface_contracts entry for that service
    (b) The consuming phase (X) task description references the contract by phase and ID
    (c) The contract includes: ID, expected class/module name, description,
        defined_in_task, and consumed_by_phases
    (d) consumed_by_phases matches the actual consuming phases found in task descriptions
    (e) **Sequential ordering:** the defining phase is in an earlier execution group
        than every phase in consumed_by_phases. Phases with interface dependencies
        MUST NOT be in the same parallel group.

    Flag: cross-phase code dependencies with no contract declared.
    Flag: "calls the helper" or "receives via injection" without referencing a specific
    contract by phase and ID.
    Flag: producing and consuming phases in the same parallel group.
```

Also update all references to the total dimension count (currently "10 dimensions" or "11 dimensions") to reflect the new total.

---

### Change 9 — Update Generation Constraints

**Location:** `.workflow/rules/planning/generation-constraints.md` → Task Descriptions + Parallel Safety sections

**Current Task Descriptions section:**

```
`tasks[].description` — PROHIBITED content:

- Method, function, or class names (`getAppState()`, `UserService`, `handleSubmit`)
- Property paths (`config.auth.tokenExpiry`, `req.body.email`)
- CLI flags or command syntax (`--verbose`, `-p 3000`, `npm run build`)
- Package/library names as implementation directives ("use lodash.debounce", "with Express router")
- Code snippets, pseudocode, or implementation algorithms
- Line numbers or file byte offsets

Task descriptions SHOULD contain: behavioral requirements, constraints, boundaries,
purpose, references to component analysis ("see analysis for existing patterns").
```

**Proposed Task Descriptions section:**

```
`tasks[].description` — PROHIBITED content:

- Private implementation details (polling intervals, internal method bodies, algorithm
  choices, internal data structure layouts)
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

Task descriptions SHOULD contain: behavioral requirements, constraints, boundaries,
purpose, references to component analysis ("see analysis for existing patterns"),
contract references for cross-phase dependencies.
```

**Current Parallel Safety section:**

```
## Parallel Safety

File cross-check after writing all phase files:

- Scan `tasks[].files` across phases in the same parallel group. If any file appears
  in two phases within the same group, move one phase to a later group.
```

**Proposed Parallel Safety section:**

```
## Parallel Safety

After writing all phase files, run two cross-checks:

**File cross-check:**
- Scan `tasks[].files` across phases in the same parallel group. If any file appears
  in two phases within the same group, move one phase to a later group.

**Interface dependency cross-check:**
- Scan `interface_contracts[].consumed_by_phases` across all phases. For each contract,
  verify that the defining phase is in an earlier execution group than every consuming
  phase. Phases with interface dependencies MUST NOT be in the same parallel group.
  If violated, move the consuming phase to a later group.
```

---

### Change 10 — Executor Prompt: Add `{received_interfaces}` Input

**Location:** `executor-prompt.md` → For Orchestrator — Data to Collect → add new row

**New row in placeholder table:**

```
| `{received_interfaces}` | Interface reports from earlier phases' executors (captured by orchestrator). Format: deterministic markdown. `None` if this phase consumes no cross-phase interfaces. |
```

**New section in For Subagent prompt** (add after "User Directives"):

```
**Received Interfaces:** *(include only if this phase consumes cross-phase interfaces)*
{received_interfaces}
These are the actual public interfaces produced by earlier phases. Use the exact class
names, method names, and signatures shown here when importing or calling these modules.
Do not invent alternative names or signatures — these are the implemented reality.
```

---

### Change 11 — Executor Output: Add `## Public Interfaces` Section

**Location:** `executor-prompt.md` → Output Format → add after `## Decisions`, before `## Discoveries`

**Proposed addition:**

```
## Public Interfaces
*(include only if this phase has `interface_contracts` declared in its phase JSON)*

For each contract declared in this phase's `interface_contracts`:

### contract-{NN}: {ClassName}
**File:** {actual file path where the class/module was created}
**Signature:**
```{language}
{class/module signature — public methods only, no bodies}
```

Report every contract listed in this phase's `interface_contracts`. Use the exact
contract ID from the phase JSON. Include only public methods — no private helpers,
no method bodies, no internal implementation details.

Example:

### contract-01: BridgeHelper
**File:** src/helpers/bridge.py
**Signature:**
```python
class BridgeHelper:
    def __init__(self, page: Page)
    async def trigger_action(self, name: str, params: dict | None = None) -> Any
    async def drain_events(self) -> list[dict]
    async def wait_for_state(self, state: str, timeout_ms: int = 10000) -> None
    async def start_event_collection(self) -> None
    async def stop_event_collection(self) -> None
```
```

**Update the For Orchestrator — Expected Output table:**

```
| `## Public Interfaces` | Per contract: ID, class name, file path, signature | Capture and forward to consuming phases' executor prompts as `{received_interfaces}` |
```

---

### Change 12 — Execute Skill: Interface Capture-and-Forward Protocol

**Location:** `execute/SKILL.md` → Step 2b: Phase Execution → add after parsing executor output

**Proposed addition (new sub-section after "Parse executor output"):**

```
**Capture public interfaces (conditional):**

If the phase JSON has non-empty `interface_contracts`:
1. Parse the executor's `## Public Interfaces` section
2. For each contract reported:
   a. Match the contract ID to the phase's `interface_contracts[].id`
   b. Store the full interface block (contract ID, class name, file path, signature)
3. These stored interfaces are forwarded to consuming phases — see "Interface
   Forwarding" below

If the executor's output is missing `## Public Interfaces` but the phase has
`interface_contracts`: escalate to user — "Phase {N} was expected to report public
interfaces for {contract IDs} but did not. The consuming phases ({consumed_by_phases})
need these interfaces. Re-run the phase or provide the interfaces manually?"
```

**New sub-section at the end of Step 2b:**

```
**Interface forwarding:**

When spawning an executor for a phase that consumes cross-phase interfaces
(its task descriptions reference contracts from other phases):

1. Collect all interface blocks captured from the producing phases
2. Assemble them into the `{received_interfaces}` placeholder:

   Interfaces from earlier phases:

   ### contract-01: BridgeHelper (from Phase 3)
   **File:** src/helpers/bridge.py
   **Signature:**
   ```python
   class BridgeHelper:
       def __init__(self, page: Page)
       async def trigger_action(self, name: str, params: dict | None = None) -> Any
       async def drain_events(self) -> list[dict]
   ```

   ### contract-02: GeminiHelper (from Phase 3)
   **File:** src/helpers/gemini.py
   **Signature:**
   ```python
   class GeminiHelper:
       def __init__(self, api_key: str)
       async def analyze_image(self, screenshot: bytes, prompt: str) -> str
   ```

3. Pass as `{received_interfaces}` in the executor prompt

If a referenced contract was not captured (producing phase failed or didn't report
it): escalate to user before spawning the consuming phase's executor.
```

---

## Impact Assessment

These 12 changes form a closed loop across the planning, review, and execution pipeline.

### Planning side (Changes 1-6, 9)

| Change | Role in the System |
|--------|--------------------|
| #1 Principle refinement | Teaches the planner the distinction between private internals and cross-phase dependencies |
| #2 New principle | Defines when dependencies must be declared, what they contain, and sequential enforcement |
| #3 Phase JSON field | Gives dependency declarations a home in the data model |
| #4 Description field update | Permits contract references in task text without conflicting with the HOW rule |
| #5 Anti-pattern | Enables pattern recognition during plan design |
| #6 Step 7 sub-step | Integrates dependency identification and sequential enforcement into the planning flow |
| #9 Generation constraints | Aligns the concrete rules file with the updated principles — prevents reviewer conflicts |

### Review side (Changes 7-8)

| Change | Role in the System |
|--------|--------------------|
| #7 Reviewer Dimension 4 update | Stops the reviewer from rejecting valid contract references |
| #8 New Reviewer Dimension 12 | Enforces dependency declarations and sequential ordering |

### Execution side (Changes 10-12)

| Change | Role in the System |
|--------|--------------------|
| #10 Executor input | Gives the consuming executor actual interfaces from earlier phases |
| #11 Executor output | Enables the producing executor to self-report its public interfaces |
| #12 Execute skill protocol | Connects production to consumption — the orchestrator captures and forwards |

### Dependency analysis — what breaks if a change is removed:

- **Without #3:** There is nowhere to declare dependencies in the JSON. Changes #2, #6, #8, and #12 reference a field that does not exist.
- **Without #7:** The reviewer flags contract references in task descriptions as Dimension 4 violations, rejecting plans that correctly use the system.
- **Without #8:** Dependencies are declarable but not enforced. Planners omit them under time pressure. Sequential ordering is not verified. The system degrades to the current state.
- **Without #6:** The planner is never prompted to identify cross-phase dependencies during plan creation. Declarations happen only when the planner remembers.
- **Without #9:** The generation constraints file contradicts SKILL.md — the planner reads both and gets conflicting rules about whether contract references are allowed.
- **Without #11:** The executor has no format for reporting public interfaces. The orchestrator has nothing to capture.
- **Without #12:** Interfaces are reported but not forwarded. Consuming phases still operate blind.
- **Without #10:** The consuming executor has no placeholder to receive interfaces. The orchestrator captures but cannot inject.

All 12 changes must be applied together to close the loop.

### What this does NOT change

- **Plan.json format** — phase dependencies and groups already exist. Sequential enforcement uses existing fields.
- **Executor internals** — how the executor implements tasks is unchanged. Only the input (receives interfaces) and output (reports interfaces) are extended.
- **Reviewer dimensions 1-11** — existing dimensions are unchanged except Dimension 4's scope refinement.
- **Analysis gate** — component analysis is unchanged.
- **State tracking** — no new state fields. Interface capture lives in the orchestrator's session context, not in state.json.
