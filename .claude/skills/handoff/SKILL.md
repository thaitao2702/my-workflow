---
name: handoff
version: 1.0.0
description: |
  Produces a deep session handoff document so a fresh Claude session can resume
  seamlessly by reading a single markdown file. Captures the user's active
  decisions (supersedence applied — latest overrides earlier), active directives
  and constraints, the north-star goal, a justified must-read file list (gated by
  the necessity test), failed approaches that should not be retried, open
  questions, and the concrete next action.

  Triggers: "/handoff", "summarize this session for next time", "save the context
  for later", "I want to continue this in a new session", "create a handoff doc",
  "checkpoint this conversation", "make a resume note", "write a handover", "dump
  context to a file", "snapshot where we are".

  Use when the user wants a portable, human-readable session summary written to
  disk for a future session (their own next session, or a teammate, or another
  agent) to read cold and continue with full direction. Do NOT use for: auto-memory
  updates (the memory system handles cross-session user/feedback/project facts);
  plan state persistence (use /execute and the plan state CLI); quick recaps
  delivered in chat (just answer inline); or PR descriptions (use git tooling).
---

# /handoff — Deep Session Handoff Document

You are producing a single markdown file that lets a brand-new Claude session pick up exactly where this one left off — without re-reading the transcript, without re-interrogating the user, and without retrying paths that already failed. The file is written for a cold reader: it must work even if the next session has zero memory of this conversation.

**Input:** `/handoff` (no arguments needed — read the conversation), or the user phrases it naturally.
**Output:** `.claude/handoffs/{YYYY-MM-DD_HHMM}-{slug}.md`

## Expert Vocabulary Payload

**Conversation Architecture:**
decision log, directive ledger, supersedence rule (latest overrides prior), decision provenance (user-stated vs assistant-inferred), conversation arc, closed loop vs open question

**Context Engineering:**
cold-start context, working set, attention budget, just-in-time loading, retrieval anchor, minimum viable context, necessity test (inclusion gate)

**Knowledge Capture:**
established fact vs assumption, blocking unknown, golden path, last known good state, failed approach (negative knowledge)

**Resume Mechanics:**
idempotent restart, replay vs continue, verification step, first concrete action, north-star goal vs current task

## Anti-Pattern Watchlist

### 1. Activity Log Instead of Decision Log
**Detection:** The handoff reads chronologically — "first we tried X, then we discussed Y, then we read Z." The next session does not need a transcript replay; it needs the current state of decisions.
**Resolution:** Reorganize by dimension (decisions, directives, files, next action), not by time. Time-ordered narrative belongs only in the small "Conversation Arc" section, and only as 2–4 sentences for orientation.

### 2. Stale-Decision Retention (Supersedence Violation)
**Detection:** The decisions table contains contradictory entries because the user changed their mind mid-session and both versions were captured. The user explicitly required: latest overrides earlier.
**Resolution:** Walk the conversation chronologically. For each decision topic, keep only the most recent user-confirmed value. If an earlier decision was reversed, drop it entirely — do not annotate "we used to think X but then…" That noise pulls the next session back toward the discarded path.

### 3. File Hoarding (Necessity Test Skipped)
**Detection:** The "Must-Read Files" list contains every file touched this session, with no reason column or with reasons like "we looked at it." The next session is forced to re-read everything, defeating the handoff's purpose.
**Resolution:** For every file, run the necessity test (see Step 4). If a fresh session can understand the goal, the constraints, AND take the right next action without reading the file, exclude it from the must-read list. Move it to "Optional Context" with a one-line description, or omit entirely.

### 4. Generic Context Instead of Specific Decisions
**Detection:** Entries like "We discussed authentication," "Talked about the database schema," "Looked at the API design." A fresh session reading this learns nothing actionable.
**Resolution:** Replace every topical mention with the specific resolution. Not "discussed auth" — "User chose JWT bearer tokens over session cookies because the mobile client cannot persist cookies (decided 2026-05-13, confirmed in message ~middle of session)."

### 5. Missing the First Concrete Action
**Detection:** The handoff explains everything but never says what to do first. The next session has to re-derive the immediate next step from the broader context.
**Resolution:** The TL;DR section must end with a "Start here" line that is a concrete, atomic action: a command to run, a specific file to read, a specific question to ask the user, or a specific edit to make. Not "continue the work" — "Read `src/auth/jwt.ts` and add the `refreshToken` field to the `Claims` interface (line ~42)."

### 6. Pasted Code Blobs
**Detection:** The handoff embeds long code snippets (>20 lines) that exist on disk and can be re-read. This bloats the file and risks staleness — code may change before the next session.
**Resolution:** Reference paths and line ranges, not contents. The exception: pseudo-code or sketches that *don't yet exist on disk* — those must be captured because they're not recoverable.

### 7. Conflating User Directives With Assistant Inferences
**Detection:** Sentences like "We decided to use Postgres" when the user never said that — the assistant inferred from context. The next session will treat the inference as a hard constraint.
**Resolution:** Two separate sections. "Active Decisions" lists only what the user explicitly stated or confirmed (cite the conversational source). "Working Assumptions" lists what the assistant inferred and the user has not confirmed. The next session knows the assumptions are still negotiable.

### 8. No Reading Priority
**Detection:** The Must-Read list has no order column, or uses random order. Reading order matters because attention budget is finite — the most consequential file should be read first.
**Resolution:** Number the must-read files. Order them by: (1) goal-defining files (specs, requirements), then (2) constraint-defining files (the code that the change must respect), then (3) implementation-target files (where the work actually lands).

## Behavioral Instructions

### Step 1: Confirm Scope and Derive Slug

1. Confirm to the user in one sentence: "Writing handoff for a fresh session to resume `{topic}` — covering decisions, directives, must-read files, and next action."
2. Derive a slug (3–6 words, kebab-case) from the dominant topic of the session. Examples: `skill-creator-design`, `auth-jwt-migration`, `plan-skill-feasibility-fix`.
3. Compute the filename: `.claude/handoffs/{YYYY-MM-DD_HHMM}-{slug}.md` using the current date/time.
4. IF `.claude/handoffs/` does not exist: create it.

### Step 2: Scan the Conversation Across All Dimensions

Read the entire conversation in your context. Extract the following dimensions in a single pass — do NOT skip any:

| Dimension | What to extract |
|-----------|-----------------|
| **North Star** | The underlying objective the user is working toward (often broader than the latest task). Look at the very first user message and any explicit goal statements. |
| **Decisions (user-confirmed)** | Every choice the user explicitly stated or accepted. Cite the conversational evidence. |
| **Working Assumptions (assistant-inferred)** | Choices made by inference, not yet confirmed. |
| **Active Directives** | User corrections still in force: "always do X," "never do Y," "stop summarizing," "use library Z." |
| **Files Read or Referenced** | Every file path that came up. Note whether read, edited, written, or merely mentioned. |
| **Knowledge Gathered** | Non-obvious things learned: project conventions, gotchas, hidden constraints, naming patterns. |
| **Failed Approaches** | Anything tried that didn't work, with WHY it failed. |
| **Open Questions** | Pending decisions blocking progress. |
| **External References** | Tickets, PRs, URLs, docs the user pointed at. |
| **Current State** | What's done, what's in progress, what's not started. |

### Step 3: Apply the Supersedence Rule

For each decision topic:
1. Walk the conversation chronologically.
2. Identify all messages where the user expressed a position on this topic.
3. Keep ONLY the most recent user-confirmed position.
4. Discard earlier reversed positions entirely. Do not write "we used to think X but…" — that pulls the next session back toward the discarded path.

WHY: The user explicitly required this. Stale decisions in a handoff cause the next session to oscillate or compromise between contradictory directions.

### Step 4: Apply the Necessity Test to Every File

For each file from Step 2's "Files Read or Referenced" list, ask three questions:

1. **Goal test:** If the next session does NOT read this file, can it still understand the goal?
2. **Constraint test:** If the next session does NOT read this file, can it still respect the user's constraints?
3. **Direction test:** If the next session does NOT read this file, can it still take the right next action?

Decision rule:
- All three YES → Exclude from must-read. Either drop entirely or move to "Optional Context" with a one-line "what's in it."
- ANY one NO → Include in must-read. The "Why" column states which test it fails — that's its justification.

WHY: A handoff that requires reading 20 files is no faster than re-deriving from scratch. The necessity test is the gate.

IF you are uncertain whether a file is must-read or optional, surface the doubt to the user: "I'm unsure whether `src/foo/bar.ts` is essential. If you skip it, you'd lose context on {specific thing}. Include it as must-read?" Do not silently include borderline files.

### Step 5: Order the Must-Read Files

Order by reading priority:
1. **Goal-defining** — specs, requirements, ticket descriptions, the user's original message paraphrased into a file
2. **Constraint-defining** — config files, type definitions, architectural docs, existing code the change must respect
3. **Implementation-target** — files that will be edited or whose contents directly inform the next action

WHY: Attention is most attentive at the start of a context window. The most consequential file goes first.

### Step 6: Compose the Handoff File

Write to the path computed in Step 1, using the template structure in `./references/handoff-template.md`. Required sections in this exact order:

1. TL;DR for Next Session (Goal / Status / Start here)
2. North Star
3. Active Decisions (latest only) — table
4. Working Assumptions (unconfirmed) — table or "None"
5. Active Directives & Constraints
6. Must-Read Files (ordered) — table with Why column
7. Optional Context — table or "None"
8. Knowledge Map (project shape, gotchas, external references)
9. Failed Approaches (do not retry)
10. Open Questions
11. Conversation Arc (2–4 sentences, orientation only)
12. Verification Before Continuing (what the next session should re-check before acting)

Read `./references/handoff-template.md` for the exact markdown skeleton with field-level guidance.

### Step 7: Self-Audit Before Showing the User

Before reporting completion, scan your own output against the Anti-Pattern Watchlist above:
- Did any decision survive that was later reversed? (Supersedence violation)
- Did any file land in must-read without a specific necessity-test justification? (File hoarding)
- Is there a concrete "Start here" action? (Missing first action)
- Are user-stated decisions clearly separated from assistant-inferred assumptions? (Conflation)
- Are there pasted code blobs longer than ~20 lines that could be a path reference? (Blob)

Fix any violations BEFORE telling the user the handoff is ready.

### Step 8: Show the User and Request Corrections

1. Tell the user the path: "Handoff written to `.claude/handoffs/{filename}`."
2. Show them the TL;DR section inline (Goal / Status / Start here).
3. Ask: "Anything I got wrong or missed? Specifically: did I capture the latest version of every decision you've made, and is there a constraint or open question I overlooked?"
4. IF the user corrects something: edit the file, do not re-derive from scratch.

## Output Format

The handoff file follows the template in `./references/handoff-template.md`. Section order is fixed; section content is filled per the rules in Steps 2–5.

The user-facing chat response after writing is short:

```
Handoff written to .claude/handoffs/{filename}.

**Goal:** {one sentence}
**Status:** {phase / blockers}
**Start here:** {first concrete action}

Anything I got wrong, or a decision/constraint I missed?
```

## Examples

### Example 1: BAD vs GOOD Decision Capture

**BAD:**
```markdown
## Decisions
- We discussed authentication options
- Talked about whether to use Postgres or MySQL
- Decided on a database
- Considered using JWT
```
Generic. Topical. No resolutions. No supersedence applied (the user changed their mind on the database mid-session and both versions are implied). The next session learns nothing actionable.

**GOOD:**
```markdown
## Active Decisions (latest only)
| # | Decision | Rationale | Source |
|---|----------|-----------|--------|
| 1 | Use JWT bearer tokens for auth (NOT session cookies) | Mobile client cannot persist cookies reliably | User stated explicitly mid-session |
| 2 | Use Postgres (NOT MySQL — earlier preference reversed) | JSONB support needed for `user_preferences` column | User reversed earlier MySQL choice after schema review |
| 3 | Refresh token TTL = 7 days, access token TTL = 15 min | Matches existing mobile session duration | User confirmed when asked |
```
Specific resolutions. Latest-only (the MySQL reversal is captured as the *current* state, not as historical churn). Each decision has a rationale and provenance. The next session can act on this without ambiguity.

### Example 2: BAD vs GOOD File Inclusion

**BAD:**
```markdown
## Files
- src/auth/jwt.ts
- src/auth/session.ts
- src/auth/middleware.ts
- src/users/model.ts
- src/api/routes.ts
- package.json
- tsconfig.json
- README.md
- docs/architecture.md
- src/db/schema.ts
- src/db/migrations/001_init.sql
- (… 12 more)
```
No order. No reasons. No necessity test applied. The next session must re-read all 22 files to figure out which ones matter, which is the same cost as starting cold.

**GOOD:**
```markdown
## Must-Read Files (ordered)
| # | Path | Why next session needs this |
|---|------|-----------------------------|
| 1 | docs/architecture.md (sections "Auth Flow" + "Token Refresh") | Defines the goal — the JWT migration must follow this flow. Skipping this fails the goal test. |
| 2 | src/auth/session.ts (lines 1–80) | Current session-cookie implementation that must be replaced. Skipping this fails the direction test — next session won't know what to remove. |
| 3 | src/users/model.ts (the `User` type, ~line 42) | Adds the `refreshToken` field here. Direction test fails without it. |

## Optional Context (skip unless needed)
| Path | What's in it |
|------|--------------|
| src/auth/middleware.ts | Existing route guards — only relevant if changing the auth header parsing. |
| src/db/schema.ts | DB schema — relevant only if user wants to persist refresh tokens server-side (open question #2). |

(Files like package.json, tsconfig.json, README.md, and unrelated routes were touched but excluded — fresh session can understand goal/constraints/direction without them.)
```
Three must-read files, each justified by which necessity test it fails. Optional files have one-line context. Excluded files are accounted for so the next session knows nothing was hidden.

### Example 3: BAD vs GOOD Next Action

**BAD:**
```markdown
## Status
We're in the middle of the JWT migration. Continue the work.
```
Useless. The next session has to re-derive what "continue" means.

**GOOD:**
```markdown
## TL;DR for Next Session
**Goal:** Replace session-cookie auth with JWT bearer tokens across the API.
**Status:** Decisions locked. `src/auth/jwt.ts` skeleton written but `refreshToken` field not yet added to the `Claims` interface. Tests not started.
**Start here:** Open `src/auth/jwt.ts:42` and add `refreshToken: string` to the `Claims` interface. Then run `npm run typecheck` to surface the call sites that need updating — that list IS the rest of the work.
```
The next session opens one file, makes one edit, runs one command, and the typecheck output enumerates the remaining work. No re-derivation needed.

## Questions This Skill Answers

- "/handoff"
- "Summarize this session so I can continue tomorrow"
- "Save the context for the next session"
- "I want to continue this in a new conversation"
- "Create a handoff doc"
- "Make a resume note for this conversation"
- "Write a handover for the next session"
- "Snapshot where we are right now"
- "Dump our progress to a file so I can pick it up later"
- "Checkpoint this conversation to disk"
- "I'm running low on context — write down everything important"
- "Help me prepare to hand this off to another agent"
- "What did we decide so far? Save it to a file."
- "Capture all the decisions and files I need next time"
