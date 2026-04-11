# Plan & Phase File Formats

Format specifications for `plan.json` and `phase-{N}.json`. Loaded at Step 7 (Write Plan Files).

---

## Plan File Format: `plan.json`

```json
{
  "name": "{feature-name}",
  "created": "{YYYY-MM-DD}",
  "status": "draft",
  "total_phases": 3,
  "total_tasks": 12,
  "summary": "Mission briefing — see field definition below",
  "scope": {
    "in_scope": ["requirement 1", "requirement 2"],
    "out_of_scope": ["explicitly excluded item"]
  },
  "component_intelligence": "Key findings from analysis that shaped this plan",
  "phases": [
    {"phase": 1, "name": "Database schema", "tasks": 3, "dependencies": [], "group": "A"},
    {"phase": 2, "name": "API endpoints", "tasks": 4, "dependencies": [1], "group": "B"},
    {"phase": 3, "name": "UI components", "tasks": 5, "dependencies": [1], "group": "B"}
  ],
  "dependency_graph_mermaid": "graph TD\n  P1-->P2\n  P1-->P3\n  P2-->P4\n  P3-->P4",
  "risks": [
    {"risk": "description", "impact": "high|med|low", "mitigation": "strategy"}
  ]
}
```

**Field definitions:**
- `name`: kebab-case feature identifier, used for directory naming
- `status`: `draft` → `reviewed` → `approved` → `executing` → `completed`
- `summary`: Mission briefing for the executor — see "Plan Summary as Mission Briefing" principle in `planning-reference.md`. Target: ~200-400 tokens.
- `scope.in_scope` / `out_of_scope`: explicit boundaries to prevent scope creep during execution
- `component_intelligence`: Key findings from analysis that shaped plan choices — see "Using Component Intelligence" principle in `planning-reference.md`.
- `phases[].dependencies`: array of phase numbers that must complete BEFORE this phase starts. Drives execution ordering.
- `phases[].group`: Parallel execution group letter (A, B, C...). Phases in the same group run simultaneously — see "Parallel Safety" principle in `planning-reference.md`.
- `dependency_graph_mermaid`: Mermaid diagram string showing phase dependencies visually
- `risks`: informed by component analysis hidden details — what could go wrong, how to mitigate. Each risk should have a concrete mitigation the executor can follow.

---

## Phase File Format: `phase-{N}.json`

```json
{
  "phase": 1,
  "name": "Database schema",
  "status": "pending",
  "group": "A",
  "depends_on": [],
  "affected_components": ["src/models/user.ts", "src/models/order.ts"],
  "goal": "Phase briefing — see field definition below",
  "tasks": [
    {
      "id": "task-01",
      "name": "Create users table",
      "description": "What to do — describes WHAT and WHY, not HOW",
      "files": ["src/db/migrations/001_users.sql", "src/models/user.ts"],
      "acceptance_criteria": [
        "Users table exists with id, email, role columns",
        "RLS policies enforce account isolation"
      ],
      "test_requirements": [
        "Insert and select user succeeds",
        "Cross-account select returns empty"
      ]
    }
  ],
  "acceptance_specs": [
    {
      "id": "spec-01",
      "description": "Account isolation enforced at database level",
      "traces_to": ["task-01"],
      "verification_type": "functional",
      "verify_by": "INSERT user under account A, SELECT under account B returns empty result set"
    }
  ],
  "interface_contracts": [
    {
      "id": "contract-01",
      "name": "UserModel",
      "description": "User data model with account isolation",
      "defined_in_task": "task-01",
      "consumed_by_phases": [2, 3]
    }
  ]
}
```

**Field definitions:**
- `group`: same as in plan.json — parallel execution group. Must match.
- `depends_on`: phase numbers that must complete first. Must match plan.json dependencies.
- `affected_components`: file paths of components this phase touches — used by `/doc-update` during reconciliation
- `goal`: **Phase briefing.** What this phase achieves and why it matters in the overall plan. An executor starting this phase should understand: what the phase produces, how it connects to other phases, what constraints apply. Include context that's specific to this phase but not repeated in every task. (e.g., "After this phase, the bridge contract is defined and any game can extend it. All files are pure TypeScript — zero engine imports.") Target: 2-4 sentences.
- `tasks[]`: Coherent units of work — see "Task Granularity" principle in `planning-reference.md`. Each is the unit of progress tracking (executor marks complete for resume).
- `tasks[].id`: Unique within the phase, format `task-NN`
- `tasks[].description`: WHAT and WHY, never HOW for internal implementation — see "Task Descriptions" principle in `planning-reference.md`. Exclude: private method bodies, polling intervals, algorithm choices, line numbers. When the task consumes a cross-phase service, reference the interface contract: "Receives BridgeHelper (Phase 3 contract-01) via constructor injection." Do not re-define signatures inline — reference the contract by phase and ID.
- `tasks[].files`: Files to create or modify — used for parallel safety checks (see "Parallel Safety" in `planning-reference.md`)
- `tasks[].acceptance_criteria`: Verifiable conditions — see "Acceptance Criteria" principle in `planning-reference.md`.
- `tasks[].test_requirements`: Specific tests to write — not "write tests" but "test that expired tokens return 401"
- `acceptance_specs[]`: Phase-level verification targets for the independent acceptance verifier — see "Acceptance Specifications" principle in `planning-reference.md`.
- `acceptance_specs[].id`: Unique within phase, format `spec-NN`
- `acceptance_specs[].description`: What behavior or property must hold. One sentence.
- `acceptance_specs[].traces_to`: Array of task-ids whose combined implementation satisfies this spec. For requirement traceability.
- `acceptance_specs[].verification_type`: `functional` (run + check output) | `structural` (code pattern must exist) | `behavioral` (system exhibits behavior under scenario)
- `acceptance_specs[].verify_by`: Concrete verification scenario. Must enable unambiguous PASS/FAIL determination. Framework-agnostic — no test framework syntax. In test mode this guides what test code to write; in reason mode this is the reasoning target.
- `interface_contracts[]`: Required only when this phase produces public APIs consumed by other phases. Omit entirely if the phase has no cross-phase consumers. Signatures are NOT included at plan time — they are captured from executor output during execution and forwarded by the orchestrator.
- `interface_contracts[].id`: Unique within the phase. Format: `contract-NN` (e.g., contract-01, contract-02).
- `interface_contracts[].name`: Expected class or module name. A planning-level coordination name — the executor should use this name unless there is a strong reason to deviate.
- `interface_contracts[].description`: One-line purpose description.
- `interface_contracts[].defined_in_task`: The task ID within this phase that creates this class or module.
- `interface_contracts[].consumed_by_phases`: Array of phase numbers that import or call this interface. Used by the reviewer to verify sequential ordering and cross-references.
