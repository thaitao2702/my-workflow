---
alwaysApply: true
---

## TDD Policy: Pragmatic

Default behavior: **write tests first**, then implement.

### When TDD applies (default)
- Business logic, data transformations, utilities
- API endpoints and route handlers
- Service layer functions
- State management logic
- Database queries and models

### Documented exceptions (tests after or skipped)
- **UI layout/styling** — Visual output is best verified by sight, not assertion
- **Config files** — Static configuration with no logic
- **Type definitions** — Interfaces/types have no runtime behavior to test
- **Prototypes/spikes** — Exploratory code explicitly marked as throwaway
- **Generated code** — Code produced by tools (migrations, scaffolding)

### Rules
- When skipping TDD, document the reason in the task or commit
- Exceptions are per-task, not per-project — the default is always TDD
- Integration tests may follow implementation when the integration surface is unknown upfront
