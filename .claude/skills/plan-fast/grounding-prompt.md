# Grounding & Feasibility Verification Prompt Template (plan-fast — single plan.md)

Drives the `feasibility-validator` agent (read-only: Read/Glob/Grep) to verify a **single markdown plan** (`plan.md`) against the REAL codebase. Unlike a plan-internal walkthrough, this subagent's job is to catch *claims about the existing code that are false* — an invented constant, a task attached to a host that can't run it, a path/symbol/field that doesn't exist — which are the feasibility bugs that actually break execution. It also does a light requirement-coverage check.

## For Orchestrator — Data to Collect

Collect paths as raw strings; pass inline blocks as raw bulleted text. Do not paste file content the subagent can read itself.

| Placeholder | Source |
|-------------|--------|
| `{plan_md_path}` | `$PLAN_DIR/plan.md` — the in-progress plan (all sections except `§feasibility`/`§risks` present) |
| `{project_overview_path}` | `.workflow/project-overview.md` — pass the path, or `None` if the file doesn't exist |
| `{requirements_in_scope}` | Inline bulleted list of confirmed in-scope requirements from Phase A (Steps 2–3). One `- requirement` per line. |
| `{user_clarification}` | Inline bulleted list of every clarification answer/constraint from Phase A. One `- answer or constraint` per line. If none, pass `- None — requirements were unambiguous as written`. |

## For Subagent — Prompt to Pass

Replace `{placeholders}` with collected values. Pass everything below this line as the subagent prompt.

You are verifying a single markdown execution plan against the REAL codebase you can read. Your job is NOT to praise the plan's structure — it is to find every place the plan asserts something about the existing code that is **false or unverifiable**, because those are the bugs that crash an executor. You have Read, Glob, and Grep over the repo. Use them aggressively.

### Phase 1 — Load context

Read these:
- `{project_overview_path}` — architectural context (skip if `None`).
- `{plan_md_path}` — the whole plan. The sections you care about most: `## Per-Capability Analysis & Approach Selection`, `## Component Notes`, `## Tasks` (Files + Done-when columns), `## Composition Audit`.

**In-scope requirements (from Phase A):**
{requirements_in_scope}

**User-clarification block (authoritative — do NOT flag gaps the user has already resolved):**
{user_clarification}

### Phase 2 — Extract every CONCRETE that touches existing code

Scan the plan and list every concrete claim about the *existing* codebase — the things that are wrong if they don't match reality. Categories:
- **Permission / access constant** — any permission/role/action string used to guard an entry point or action.
- **Host / attachment point** — any claim that a hook/listener/subscription/background task "runs in X" or "attaches to X" — verify the named host actually exists, can host it, and lives inside the runtime contexts the code needs (DI container / store / provider / session scope).
- **Injection / trigger point** — any existing handler/callback/function the plan hooks new behavior into (e.g. a post-save success handler).
- **Existing file path** — any non-`[new]` path the plan says it will modify.
- **Existing symbol / hook / component** — any function, hook, component, or export the plan reuses by name.
- **API endpoint / response field** — any endpoint or response-field name the plan reads or extends as if it exists.

A `[new]` file the plan creates is NOT a concrete-to-verify (it's the plan's output) — skip those. Verify only references to things that must *already* exist.

**Also flag two failure modes that are NOT about a wrong symbol:**
- **Core decision left DEFERRED** — the plan punts a load-bearing design choice to the executor ("locate the intercept point", "add a host if none exists", "find the right host") instead of committing to a real candidate. List each; from the codebase, name the best real candidate the plan SHOULD commit to. A deferred core decision is a Completeness/Actionability hole even when nothing is technically "wrong."
- **Lifecycle-unviable host** — a host that exists and is in-context but won't survive the feature's required lifetime: e.g., a background task or persistent listener attached to a short-lived scope (a view/request/screen) that is torn down before the work completes, so it dies before doing its job. Check the host's lifecycle against what the feature needs (outlive the triggering screen? run across the session? fire after the entry point exits?).

### Phase 3 — Verify each concrete against the codebase

For each extracted concrete, grep/glob/read to confirm it. Classify:
- `VERIFIED` — found it; cite the real `path:line`.
- `WRONG` — the plan's claim is inaccurate (wrong layer, wrong host, or the named host sits outside the runtime context the code needs). **Supply the correct real analog** with `path:line` (e.g., "the named entry point is outside the required context and can't host this; the real long-lived host is `<X>` at `<path:line>`").
- `INVENTED` — the plan asserts a specific name/constant that exists **nowhere** in the codebase (e.g. a permission string with zero matches). Name the nearest **real** analog the plan should reuse instead, with `path:line`.
- `LIFECYCLE_WRONG` — the host exists and is in-context but won't survive the feature's required lifetime (attached to a scope torn down before the work completes). Name the correct **long-lived** host with `path:line` (e.g., the app shell / root layout / service layer).
- `OVER_DEFERRED` — a core design decision the plan punted instead of committing. Name the best real candidate (with `path:line`) the plan should commit to, so the orchestrator can replace the deferral with a grounded commitment + stated assumption.
- `UNVERIFIABLE` — can't confirm or deny from the codebase (depends on an external system, or genuinely absent); recommend the plan **defer** it to executor-discovery rather than assert it. (Reserve this for non-core specifics; a core decision that's merely uncertain is `OVER_DEFERRED`, not `UNVERIFIABLE`.)

When uncertain whether something is `VERIFIED` or `WRONG`/`LIFECYCLE_WRONG`, lean toward the defect and explain — a false alarm is cheap; a missed crash or a poller that never runs is not.

### Phase 4 — Light coverage check

One row per in-scope requirement: name the task(s) that deliver it (`Ph<X>/task-NN`) and verdict `COVERED` / `PARTIAL` (name the missing sub-step) / `MISSING`. Stay at the "which task delivers this" level — do NOT re-verify implementation detail here (Phase 3 already did the grounding).

### Phase 5 — Output in this EXACT format (terse — no prose padding)

```
## Status
**Result:** GROUNDED | CORRECTIONS_NEEDED
**Concretes:** verified {V} / wrong {W} / invented {I} / lifecycle_wrong {L} / over_deferred {O} / unverifiable {U}
**Coverage:** {C}/{Total} requirements COVERED

## Grounding Table
| Concrete (as written in plan) | Category | Plan Location | Verdict | Real analog / evidence (path:line) |
|-------------------------------|----------|---------------|---------|------------------------------------|
| `<INVENTED_CONSTANT>` | permission | Ph4/task-01 | INVENTED | no match in codebase; reuse `<REAL_SIBLING_CONSTANT>` — `<path:line>` |

## Coverage Check
| Requirement | Delivering Task(s) | Verdict | Gap |
|-------------|--------------------|---------|-----|
| {requirement} | Ph1/task-02 → Ph2/task-01 | COVERED ∣ PARTIAL ∣ MISSING | {gap or —} |

## Escalations
| Type | Description |
|------|-------------|
| {none ∣ ambiguous_requirement ∣ external_unknown} | {details with citation} |
```

**Result rule:** `GROUNDED` only if there are **zero** `WRONG`, `INVENTED`, `LIFECYCLE_WRONG`, and `OVER_DEFERRED` concretes AND every requirement is `COVERED`. Otherwise `CORRECTIONS_NEEDED`. `UNVERIFIABLE` items alone do not force `CORRECTIONS_NEEDED` (they become deferrals), but list them.

**Format rules:**
- Every `WRONG`/`INVENTED` row MUST supply a real analog with `path:line` — a finding with no fix is useless.
- Keep it terse: the Grounding Table + Coverage Check + Status. No scenario narratives, no per-question evidence essays.
- Write `| none | none |` in Escalations if nothing applies; never omit the section.

## For Orchestrator — Expected Output

| Section | Key Fields | Parse For |
|---------|-----------|-----------|
| `## Status` | `**Result**`: GROUNDED ∣ CORRECTIONS_NEEDED; concrete + coverage counts | Decide: finalize vs fix |
| `## Grounding Table` | `Concrete`, `Category`, `Plan Location`, `Verdict`, `Real analog` | `WRONG`/`INVENTED` → replace with the real analog; `LIFECYCLE_WRONG` → re-point the mount to the persistent host; `OVER_DEFERRED` → replace the deferral with a grounded commitment + stated assumption; `UNVERIFIABLE` → convert to a (non-core) deferral |
| `## Coverage Check` | `Requirement`, `Delivering Task(s)`, `Verdict`, `Gap` | For each `PARTIAL`/`MISSING`: Edit `§tasks` to add/strengthen the delivering task |
| `## Escalations` | Type, Description | If any non-`none` rows: present to user before continuing |

**Orchestrator action by Result:**
- `GROUNDED` → record the terse summary in `§feasibility` (Coverage Check table + the one-line grounding result); fold any `UNVERIFIABLE` deferrals into `§risks`; proceed to Step 10.
- `CORRECTIONS_NEEDED` → apply every `WRONG`/`INVENTED` fix and `PARTIAL`/`MISSING` coverage fix via tagged-block Edits, then re-spawn (**max 2 rounds total**). If concretes still can't be grounded after 2 rounds, convert them to explicit deferrals, note in `§risks`, and proceed.
