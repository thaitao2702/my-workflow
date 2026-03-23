---
alwaysApply: true
---

## Code Quality Rules (Language-Agnostic)

### Type Safety & Correctness
- Use the strongest type system available in the language
- Avoid escape hatches (any in TS, Object in Java, interface{} in Go) — use proper types
- Function signatures should be self-documenting (clear parameter and return types)

### Error Handling
- Never swallow errors silently (no empty catch/except/rescue blocks)
- Errors should propagate with context (what operation failed + why)
- External API boundaries must handle failures gracefully

### Security
- No hardcoded secrets, API keys, or passwords in source code
- User input must be sanitized/validated at system boundaries
- Database queries must use parameterized queries / prepared statements
- Auth checks on every protected endpoint/route

### Testing
- Tests must have meaningful assertions (not just "doesn't throw/crash")
- Test file location should follow project convention
- Test names must describe behavior, not implementation details

### Code Hygiene
- No commented-out code (use version control history)
- No dead code (unused functions, unreachable branches)
- No debug output in production code (use proper logging)
- Consistent import/include ordering
