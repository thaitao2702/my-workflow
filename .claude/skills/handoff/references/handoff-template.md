# Handoff File Template

The exact markdown skeleton to write to `.claude/handoffs/{YYYY-MM-DD_HHMM}-{slug}.md`. Section order is fixed. Field-level guidance is in HTML comments — strip them before writing the final file.

```markdown
# Session Handoff — {topic} ({YYYY-MM-DD})

<!-- Filename example: 2026-05-13_1430-auth-jwt-migration.md -->

## TL;DR for Next Session

**Goal:** {one sentence — the underlying objective, not just the latest task}
**Status:** {phase / what's done / what's blocked — one or two sentences}
**Start here:** {ONE concrete atomic action — a file+line to open, a command to run, a question to ask. Not "continue the work."}

## North Star

{2–4 sentences. The broader objective the user is working toward. Often inferable from the very first user message of the session, refined by later clarifications. Distinguish from the immediate task — the immediate task is a step *toward* the north star.}

## Active Decisions (latest only)

<!-- Apply the supersedence rule. If a decision was reversed mid-session, keep ONLY the latest version. Do not annotate "we used to think X." -->

| # | Decision | Rationale | Source |
|---|----------|-----------|--------|
| 1 | {specific resolution, not a topic} | {why the user chose this} | {User stated explicitly / User confirmed when asked / User reversed earlier choice} |
| 2 | … | … | … |

<!-- If no user-confirmed decisions yet, write "None — all direction is still working assumption (see below)." -->

## Working Assumptions (assistant-inferred, unconfirmed)

<!-- Things the assistant assumed because the user didn't push back. Surface them so the next session knows they're still negotiable. -->

| # | Assumption | Basis | Confirm with user? |
|---|------------|-------|--------------------|
| 1 | {what was assumed} | {why — context clue, project convention, default} | Yes / Low priority |

<!-- "None" if everything in play is user-confirmed. -->

## Active Directives & Constraints

<!-- User corrections still in force. Format: "{rule} — Why: {reason} — How to apply: {when it kicks in}" -->

- {Directive 1}
- {Directive 2}

<!-- "None" if the user has not issued corrections this session. -->

## Must-Read Files (in order)

<!-- Apply the necessity test. Order: goal-defining → constraint-defining → implementation-target. -->

| # | Path (with line range if narrow) | Why next session needs this |
|---|----------------------------------|-----------------------------|
| 1 | {path}:{lines} | {Specific necessity-test failure: "Defines the goal — skipping fails the goal test" / "Current implementation that must be replaced — fails direction test" / "Constraint that the change must respect — fails constraint test"} |
| 2 | … | … |

## Optional Context (skip unless needed)

| Path | What's in it (one line) | When to read |
|------|-------------------------|--------------|
| {path} | {brief description} | {trigger condition: "if changing auth header parsing" / "if user wants server-side refresh tokens"} |

<!-- "None" if every relevant file is must-read. -->

## Knowledge Map

**Project shape:**
- {key components, naming conventions, architectural patterns discovered or confirmed this session}

**Gotchas (non-obvious behaviors):**
- {hidden constraint, surprising behavior, trap to avoid — with file:line if applicable}

**External references:**
- {Tickets, PRs, doc URLs the user mentioned. Format: `{label}: {URL or ID} — {why it matters}`}

## Failed Approaches (do not retry)

<!-- Negative knowledge. The point is to prevent the next session from spending time on dead paths. -->

| Approach | Why it failed | What was done instead (or what to try) |
|----------|---------------|----------------------------------------|
| {what was tried} | {specific failure mode — error, conflict, user rejection} | {alternative path or "still open"} |

<!-- "None" if no dead-end paths this session. -->

## Open Questions

<!-- Pending decisions actively blocking progress. Each must name what info is needed and from whom. -->

- **{Question}** — Needs: {who answers, what info would resolve it} — Blocking: {what work is paused on this}

<!-- "None" if nothing is blocked. -->

## Conversation Arc

<!-- 2–4 sentences. Orientation only. NOT a transcript. Describes where we started, the key turn(s), and where we are now. The next session reads this last, as a sanity check on whether the structured sections above match the spirit of the conversation. -->

{Narrative paragraph}

## Verification Before Continuing

<!-- 2–3 bullets the next session should perform BEFORE acting on the handoff. The handoff is a snapshot; reality may have moved. -->

- {Re-read X to confirm it still says Y — handoff was written at {time}, code may have changed}
- {Run `git log --since="{handoff time}"` to see if anything landed since}
- {Confirm with user: "Still want to proceed with {decision N}? Anything changed since last session?"}

---

*Handoff generated {YYYY-MM-DD HH:MM} by /handoff skill. Edit by hand to correct or extend.*
```

## Field-Level Guidance

### TL;DR — the most-read section

The next session reads TL;DR first and may stop there if the goal is small. Treat the three lines as the highest-attention real estate in the document:

- **Goal:** ends in a verb-phrase that names the deliverable. Bad: "auth stuff." Good: "Replace session-cookie auth with JWT bearer tokens across the API."
- **Status:** distinguish "done / in progress / not started" explicitly. If blocked, name the blocker.
- **Start here:** must be atomic. If you can't reduce it to one action, the handoff isn't ready — go back and resolve the open question that prevents naming the next action.

### Decisions vs Working Assumptions

The split exists because the next session will treat anything in "Active Decisions" as a hard constraint. False positives there cause the next session to refuse user requests that contradict decisions the user never actually made.

Test for placement:
- Did the user explicitly state, accept, or confirm this? → Active Decisions
- Did the assistant pick this and the user didn't object (but also didn't engage)? → Working Assumptions

### Necessity Test — the file inclusion gate

For each file:

| Test | Question |
|------|----------|
| Goal test | If next session does NOT read this, can it still understand the goal? |
| Constraint test | If next session does NOT read this, can it still respect the user's constraints? |
| Direction test | If next session does NOT read this, can it still take the right next action? |

- All three YES → exclude from must-read (move to Optional or omit)
- ANY NO → must-read; the failed test name goes in the "Why" column

When uncertain, surface the doubt to the user — do not silently include borderline files.

### Failed Approaches — write WHY, not just WHAT

"Tried using library X" is useless. "Tried using library X — fails because it requires Node 20 and project pins Node 18" prevents the next session from re-trying the same dead path.

### Verification Before Continuing — the staleness guard

A handoff is a snapshot. The next session may run hours or days later. The verification section is the bridge between snapshot-time state and real-time state. Always include:

1. A re-read instruction for the most consequential file
2. A `git log` or equivalent staleness check
3. A user-confirmation question for the top decision (in case the user changed their mind off-session)
