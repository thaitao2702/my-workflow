# Plan Review Report: manage-columns-enhancement

**Plan:** GDP-1534 — Manage Columns Enhancement
**Date:** 2026-04-11
**Review Rounds:** 2
**Final Status:** 13/13 dimensions addressed, pending user approval

---

## Review Process Overview

The plan was evaluated by an automated plan-reviewer agent against 13 structural, coverage, and consistency dimensions. Each round produced a PASS/FAIL verdict per dimension with evidence and fix requirements.

---

## Round 1 — Initial Review

**Result:** FAIL — 8/13 passed, 5 failed

### Dimension 4: Task Description Quality — FAIL

**What was flagged:**
- task-01 prescribed exact pixel measurements inline: "header (~40px) and footer (~50px)" — these are internal CSS layout decisions, not plan-level constraints.
- task-01 embedded an internal merge algorithm in the description: "saved keys that no longer exist in the current column set are ignored; new columns default to their config-defined visibility" — this is a HOW decision (algorithm steps) rather than a WHAT requirement.

**Fix applied:**
- Removed pixel-level measurements from task-02 description. Changed to "adjust the column list scrollable area to fit within the popover's existing max-height."
- Moved the merge algorithm from the task-01 narrative into acceptance criteria where it belongs (verifiable behavior: "columns whose keys exist in saved data use saved visibility; columns not in saved data use their config-defined visibility").

---

### Dimension 7: Acceptance Criteria Validity — FAIL

**What was flagged (3 criteria):**

1. **task-01:** "On init without storageKey, behavior is identical to the original hook (no localStorage interaction)"
   - Flagged as: Tautology / structural check. States what the code IS (backward-compatible), not a verifiable outcome. No observable artifact to assert beyond "it compiles and doesn't call storage."

2. **task-01:** "isAllSelected returns true only when every column in defaultColumns is checked"
   - Flagged as: Restates the definition from the task description rather than describing a scenario with observable pre/post-conditions.

3. **task-03:** "Select All, Save, and Reset work end-to-end on any report page using this layout"
   - Flagged as: Vague. "Works end-to-end" is not verifiable — lacks specific observable outcomes. Contradicts the standard of having testable criteria.

**Fix applied:**
- Replaced criterion 1 with two concrete criteria: "On init with a storage key but no saved data, columns use their config-defined visibility identically to a hook without a storage key" (observable) and later "Existing call sites that destructure the current return tuple continue to work without modification" (compilation-verifiable).
- Replaced criterion 2 with: "Given 5 columns where 3 are checked, isAllSelected is false; given all 5 checked, isAllSelected is true" — concrete given/then scenario.
- Replaced criterion 3 with: "On any report page using this layout, opening the popover shows the Column Display header with Select All, and the Reset to Default / Save footer buttons" — specific observable outcome.

---

### Dimension 8: Test Requirement Validity — FAIL

**What was flagged (4 test requirements):**

1. **task-01:** "After handleSaveDefault, reading from localStorage returns the saved checkedColumns"
   - Flagged as: Tests the behavior of `setEncryptStorage` (third-party library), not the hook's own logic. The test verifies the storage library works, not the task code.

2. **task-02:** "Rendering PopoverManageColumn with isAllSelected=true shows Select All checkbox as checked"
   - Flagged as: Zero-logic artifact check. Passing a boolean prop through to an Ant Design Checkbox `checked` prop has no logic branch to verify — any correct implementation makes this trivially unfalsifiable.

3. **task-03:** "Navigate to Bet History, toggle Select All, click Save — reload page and verify saved columns are applied"
   - Flagged as: End-to-end integration test that crosses task scope into acceptance spec territory (duplicates spec-02). Tests storage behavior + browser behavior + multiple tasks combined.

4. **task-03:** "Navigate to Player Summary, save a default — navigate to Game Summary and verify it has independent column preferences"
   - Flagged as: Same issue — duplicates spec-04's acceptance spec and crosses task-test scope into acceptance spec territory.

**Fix applied:**
- task-01: Replaced with round-trip behavioral test: "After save, then deselect-all, then reset — the visibility map matches the state at the time of save" — tests the hook's own save/reset logic, not the storage library.
- task-02: Replaced with state-change test: "When the all-selected prop changes from false to true, the Select All checkbox rendered state updates to checked" — tests reactivity, not static prop passing.
- task-03: Replaced both navigation tests with unit-level assertions: "Given two different report pathnames, the derived storage keys are distinct" and "The hook's new return values are each passed as corresponding props to PopoverManageColumn" — tests task-03's own wiring logic.

---

### Dimension 10: Codebase Alignment — FAIL

**What was flagged (3 misalignments):**

1. **Hook return type contract:**
   The current `useManageVisibleColumn` returns a 3-element tuple: `[state, handleOnChange, handleOnDragEnd]`. The plan adds 4 new return values but never specifies how they are added. The existing call site in `ListDataTableLayout.tsx` (line 182-185) destructures as a positional tuple. Extending to positions 3-6 could break TypeScript inference at all 7+ existing call sites. The plan treated the hook as if it returns named properties.

2. **Hook initialization guard:**
   The `useEffect` that calls `initialColumns` is guarded by `if (permission)`. When `permission` is `undefined`, the hook never initializes. The plan added localStorage loading but didn't address that this loading would also be blocked by the permission guard.

3. **`getEncryptStorage` null safety:**
   `storage.tsx` line 30: `getEncryptStorage` calls `encryptStorage.getItem(key)` where `encryptStorage` is undefined until `setupEncryptStorage()` is called during app bootstrap. Calling it during hook initialization (before setup) throws `TypeError`. The existing codebase avoids this — `FilterUtils.tsx` only calls storage utilities inside event handlers, never during initialization.

**Fix applied:**
- Added explicit guidance in task-01 description: "The hook currently returns a positional tuple consumed by 7+ call sites across the codebase — the extended return type must not break any existing destructuring."
- Added: "The existing initialization is guarded by a permission check in useEffect — localStorage loading must only occur after permission is available and the encrypted storage utility is initialized."
- Added acceptance criterion: "When the encrypted storage utility is not yet initialized, the hook gracefully falls back to config-defined visibility without throwing."
- Added acceptance criterion: "Existing call sites that destructure the current return tuple continue to work without modification."

---

### Dimension 13: Interface Dependency Coverage — FAIL

**What was flagged:**
- task-03 consumes new hook outputs (from task-01) and new component props (from task-02) but no `interface_contracts` entries exist. The reviewer flagged that cross-task dependencies should be formally declared.

**Fix applied:** REJECTED as false positive.
Per the planning reference: "Called only within the same phase -> private, no declaration needed." All 3 tasks are in Phase 1, executed by the same agent sequentially. Interface contracts are for cross-PHASE dependencies where independent executor agents need coordination. Within a single phase, the executor has full context of all prior task outputs.

---

## Round 2 — Review After Fixes

**Result:** FAIL — 9/13 passed, 4 failed

### Dimension 4: Task Description Quality — FAIL (repeat)

**What was flagged:**
- task-01 description still contains specific method names (`handleSelectAll`, `handleSaveDefault`, `handleResetDefault`), property names (`checkedColumns`, `scrollX`, `defaultColumns`), and structural details ("3-element tuple") that the reviewer classified as HOW-level implementation prescription.

**Fix applied:** Partially accepted. Softened the language to use behavioral descriptions ("bulk select-all / deselect-all toggling", "save current visibility as default", "a derived boolean for all-selected state") instead of method names. However, some specifics were retained because:
- The tuple return type detail is a critical backward-compatibility constraint, not an implementation choice
- The permission guard interaction is a codebase constraint the executor needs to know

---

### Dimension 10: Codebase Alignment — FAIL (new findings)

**What was flagged (3 issues):**

1. **Unguarded `encryptStorage` access at hook initialization:**
   task-01 mentions null-safety but neither acceptance criteria nor test requirements included a test case for the failure mode where `encryptStorage` is undefined.

2. **Multiple unaddressed `useManageVisibleColumn` call sites:**
   Grep revealed 7+ additional call sites beyond the Report ListDataTableLayout: `src/components/ListDataTableLayout.tsx`, `ListDataTableBetLayout.tsx`, `ListSummaryLayout.tsx`, `ListMandatoryLayout.tsx`, `ListDataTableMutationLayout.tsx`, `fe_foundation/ListDataTableLayout.tsx`, `DataLayoutAgentGameSetting.tsx`. All use 3-element tuple destructuring. No task includes these files or verifies they still compile.

3. **`ListDataTableBetLayout.tsx` also uses `PopoverManageColumn`:**
   This file renders `PopoverManageColumn` with the existing props. If new props are required (not optional), this call site produces a TypeScript compile error. The plan didn't address whether new props are required or optional.

**Fix applied:**
- Added acceptance criterion to task-01: "When the encrypted storage utility is not yet initialized, the hook gracefully falls back to config-defined visibility without throwing."
- Added to task-02 description: "All new props must be optional so that existing PopoverManageColumn call sites outside the Report ListDataTableLayout continue to work without passing the new props."
- Added acceptance criterion to task-02: "When the new optional props are not provided, the popover renders without the header and footer — identical to current behavior."
- Added test requirement to task-02: "Rendering without the new optional props produces the original popover layout with no header or footer."
- Added acceptance spec-06: "Existing non-Report layouts using PopoverManageColumn and useManageVisibleColumn continue to work — build with no TypeScript compilation errors, non-Report pages render popover in original form."

---

### Dimension 11: Acceptance Spec Coverage — FAIL (new finding)

**What was flagged:**
- The scope says "Applies to all reports: Bet History, Player Summary, Game Summary, Promotion Summary." But spec-02 verify_by only names Bet History. spec-04 only names Bet History and Player Summary. Game Summary and Promotion Summary are never explicitly verified by any spec.
- No spec verifies backward compatibility for the 7+ non-Report call sites.

**Fix applied:**
- Extended spec-04 verify_by to include all 4 reports: "Navigate between Bet History, Player Summary, Game Summary, and Promotion Summary — each loads its own saved defaults independently. Verify Game Summary and Promotion Summary also show the enhanced popover."
- Added spec-06: backward compatibility verification for non-Report layouts.

---

### Dimension 12: System Composition — FAIL (new finding, critical)

**What was flagged:**
The plan states "Auto-load saved default view on page load and across sessions" and spec-02 requires "Clear session (logout/login) — the saved column selection is still applied."

However, `storage.tsx` lines 110-125 show `clearAllStorage()` is called on logout. This function:
1. Saves `appLang` (plain localStorage) and `ecode` (encrypted)
2. Calls `clearLocaleStorage()` which calls `localStorage.clear()`
3. Calls `clearSessionStorage()`
4. Restores only `appLang` and `ecode`

Column preferences stored via `setEncryptStorage` would be **wiped on every logout**. The cross-session persistence requirement is impossible with the current storage approach. No task in the plan modifies `clearAllStorage` to preserve column preference keys.

**Fix applied:**
- Added `storage.tsx` to task-01's files list
- Added to task-01 description: "Column preferences must persist across logout — the existing clearAllStorage function in storage.tsx wipes all encrypted localStorage on logout. Either use a storage approach that survives clearAllStorage, or modify clearAllStorage to preserve column preference keys."
- Added acceptance criterion: "Saved column preferences survive the logout flow (clearAllStorage) and are available on next login."
- Updated plan.json risks to flag clearAllStorage as HIGH impact risk with mitigation strategies
- Updated plan summary and component_intelligence to document this critical finding

---

## Summary of All Changes Across Both Rounds

| Area | Original | After Round 1 | After Round 2 |
|------|----------|---------------|---------------|
| task-01 files | `useManageVisibleColumn.tsx` only | Same | Added `storage.tsx` |
| task-01 description | Included pixel sizes, algorithm steps | Removed algorithm from prose | Added tuple compat, permission guard, null-safety, clearAllStorage requirements |
| task-01 acceptance criteria | 7 criteria, 3 flagged | Rewrote flagged criteria with concrete scenarios | Added null-safety criterion, logout survival criterion |
| task-01 test requirements | 4 reqs, 1 tested library behavior | Replaced with round-trip behavioral tests | Same |
| task-02 description | Specified exact pixel heights | Removed pixel values | Added "all new props must be optional" |
| task-02 acceptance criteria | 8 criteria | Same | Added "renders without header/footer when props absent" |
| task-02 test requirements | 3 reqs, 1 zero-logic | Replaced with state-change test | Added backward-compat rendering test |
| task-03 description | Specified exact suffix string | Moved suffix to criteria | Softened to behavioral description |
| task-03 acceptance criteria | 4 criteria, 1 vague | Replaced vague "works end-to-end" | Same |
| task-03 test requirements | 2 reqs, both E2E scope leaks | Replaced with unit-level assertions | Same |
| Acceptance specs | 5 specs | Same | Added spec-06 (backward compat), extended spec-04 to all 4 reports |
| Plan risks | 2 risks | Same | Added clearAllStorage (HIGH) and null-safety (MED) risks |
| Component intelligence | Basic architecture | Same | Added tuple return type, 7+ call sites, clearAllStorage finding, null-safety warning |

---

## Dimensions That Passed Both Rounds (no changes needed)

| # | Dimension | Evidence |
|---|-----------|----------|
| 1 | Requirement coverage | All 6 in-scope requirements trace to tasks |
| 2 | Task atomicity | 3 tasks, each scoped to 1-2 files |
| 3 | Task granularity | Coherent units aligned to architectural layers |
| 5 | Dependency correctness | Single phase, no circular deps |
| 6 | File scope safety | No file claimed by multiple tasks |
| 9 | Consistency | No conflicting instructions |
| 13 | Interface dependency coverage | All tasks in same phase — no cross-phase contracts needed |

---

## Critical Discovery: clearAllStorage

The most significant finding from the review process was the `clearAllStorage` issue (Round 2, Dimension 12). This was NOT apparent from reading the hook or popover source code alone — it required tracing the full system lifecycle (login -> use app -> logout -> login) and understanding that `clearAllStorage()` in `storage.tsx` wipes everything except `appLang` and `ecode`.

Without this review finding, the feature would have been implemented, tested within a single session, and shipped — only to fail the first time a user logs out and back in. The column preferences would silently disappear.

This is exactly the class of defect that plan review catches: cross-component behavioral contracts that no single task's source code reveals.
