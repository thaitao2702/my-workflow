---
description: |
  Simple, low-ceremony planning skill. Produces a plain-markdown execution plan
  through structured requirements gathering, codebase exploration, task design,
  and feasibility walkthrough — written to a single editable `.md` file. No JSON
  schemas, no subagent review, no formal decomposition tables.

  Accepts requirements from text, file path, GitHub issue, GitLab issue, or
  Jira ticket — invokes the matching skill to fetch external sources.

  Triggers: "/plan-quick [requirement]", "simple plan", "lightweight plan",
  "low-overhead plan", "markdown plan", "plan this without ceremony",
  "quick plan from jira / gh / gitlab", "I want a plan I can edit by hand".

  Use when you want a plan you can edit by hand, share as a doc, or discuss
  with collaborators. Skip when you need machine-readable plan files, formal
  multi-dimension review, or multi-phase coordination.
---

# /plan-quick — Simple Markdown Plan

You are creating a focused, human-readable execution plan as a single markdown file. The plan is only as good as the requirements it's built on — invest in clarifying the requirements rigorously before composing tasks. Skip the heavy decomposition machinery; produce a plan a reader can scan end-to-end and edit by hand. Plan size doesn't matter — even a large plan can be expressed simply if the user wants a low-ceremony artifact.

**Input:** `/plan-quick "text"`, `/plan-quick ./path/to/file.md`, `/plan-quick gh:123`, `/plan-quick gl:456`, `/plan-quick jira:PROJ-789`
**Output:** `.workflow/plans/{YYMMDD}-{slug}/plan.md`

## Anti-Pattern Watchlist

### Under-clarifying
- **Detection:** Skipping the Step 2 questionnaire categories because "the requirement looks clear," then producing a plan that misreads the user's intent. The questionnaire exists to surface gaps the user assumed obvious; assuming alignment without checking is the most likely failure of this skill.
- **Resolution:** Always run Step 2 explicitly. Skip categories that genuinely don't apply, but state which ones you skipped and why. Never skip the whole step.

### Planning blind
- **Detection:** Generating the task list in Step 4 without first reading the project overview and the actual affected files in Step 3.
- **Resolution:** Step 3 is non-negotiable. The plan must be grounded in what's actually in the codebase, not in assumptions about what's there.

### Vague acceptance criteria
- **Detection:** Writing "works correctly", "looks good", "behaves as expected" as acceptance criteria.
- **Resolution:** Every acceptance criterion must be verifiable by running something concrete — a command, a test scenario with defined input/output, a query, a manual scenario with a defined observable outcome.

### Skipping the user checkpoint
- **Detection:** Writing `plan.md` immediately after the feasibility walkthrough without showing the full plan to the user.
- **Resolution:** Step 6 is non-negotiable. The user is the only review this skill has.

### Performative feasibility walkthrough
- **Detection:** Filling the Step 5 trace and premortem with vague, plan-agnostic risks ("the implementation might have bugs", "the user might not like it"). This converts a real safety net into noise.
- **Resolution:** Every premortem failure mode must cite a specific task, file, constraint from Step 3, or requirement detail from Step 2. If you can't cite the source, the risk isn't grounded enough to include.

## Step 1: Parse Input

Determine the source and extract the initial requirements:

| Input Pattern | Action |
|--------------|--------|
| `"quoted text"` or plain text | Use directly as the initial requirement |
| `./path/to/file.md` | Read the file, extract the initial requirement |
| `gh:123` or GitHub URL | Use the Skill tool to invoke `/github` with the issue reference |
| `gl:123` or GitLab URL | Use the Skill tool to invoke `/gitlab` with the issue reference |
| `jira:PROJ-456` | Use the Skill tool to invoke `/jira` with the ticket ID |

The skill invocations return issue/ticket content as clean markdown. Treat that as your starting requirement text — Step 2 will clarify it.

## Step 2: Requirements Gathering

A plan is only as good as the requirement behind it. Run a structured questionnaire covering the gap categories below. **Do not skip this step.** Skip individual categories that genuinely don't apply, but state which you skipped and why.

Rules:
- Questions must be **specific to the requirement at hand**, not generic. Bad: "What about errors?" Good: "When the payment validation fails on POST /orders, should the order persist as 'pending', or be discarded entirely?"
- Group questions into batches of 3-5 per round to avoid overwhelming the user
- Maximum 3 rounds of questions. If answers raise new questions, ask them in the next round.
- After all rounds complete, **re-state the consolidated requirements back to the user in your own words** as a numbered list. Ask "Is this the correct understanding?" Wait for explicit confirmation before proceeding to Step 3.

**Gap categories to cover** (skip what genuinely doesn't apply; state which you skipped):

1. **Success condition** — What does "done" look like concretely? What output, behavior, or observable state proves the work is complete?
2. **Input shape** — What inputs does this work consume? Format, source, validation rules, examples?
3. **Output shape** — What outputs does it produce? Format, destination, error response shape?
4. **Edge cases & errors** — What happens for invalid input, empty state, malformed data, missing dependencies, concurrent access, partial failures?
5. **Permissions / auth** — Who can perform this action? Role checks, ownership rules, public vs authenticated?
6. **Existing data** — Backfill with defaults, migrate to new shape, ignore, or transform existing data?
7. **Performance / scale** — Expected volume, response time targets, batching, pagination, rate limits?
8. **Validation rules** — What invalidates input? Where should validation run (client, server boundary, deep in service)?
9. **UI/UX details** — Loading states, empty states, error messages, accessibility, mobile/desktop differences? (Only if UI is involved.)
10. **Dependencies** — Does this require new libraries, services, env vars, config keys, feature flags?
11. **Out of scope** — What's explicitly NOT included? Helps prevent scope creep during execution.
12. **Observability** — Logging, metrics, tracing needs?

For each round, present questions clearly and grouped by category. Example format:

> "I have some clarification questions before planning:
>
> **On success condition:**
> 1. Should the export endpoint return the full CSV inline, or return a download URL that streams from a temporary store?
>
> **On edge cases:**
> 2. If the date range has zero matching records, return 200 with an empty CSV (headers only) or 404?
> 3. ..."

After confirmation of the consolidated requirements, proceed to Step 3.

## Step 3: Read Project Overview + Explore Codebase

Ground the plan in what's actually in the codebase. Three sub-steps:

1. **Read `.workflow/project-overview.md`** for architectural context — what the project is, the major modules, the conventions in use. If the file doesn't exist, note that and proceed without it.

2. **Explore the codebase** using Glob/Grep to find every file and module the requirement might touch:
   - Grep for symbols, function names, types, or domain terms mentioned in the requirement
   - Glob for directories or file types relevant to the change (e.g., `src/api/**/*.ts` for an API change, `src/models/**` for a schema change)
   - Use the existing project structure (from the overview) as the map for what to explore
   - Cast a wide net at first — better to find a file you don't need than to miss one you do

3. **Read the identified files.** For each file you read, note inline any constraint or hidden behavior that affects the plan. Examples: "function silently clamps date ranges to 90 days — relevant if requirement wants full-range export", "service uses an event bus to notify downstream — implies any state change must publish an event", "validation runs in middleware, not the controller — new endpoint must register middleware".

The output of this step is your mental model of the affected surface area + a set of inline notes. No formal table. The notes feed into Step 4 (which files each task touches) and Step 4's Component Notes section in plan.md.

## Step 4: Generate Task List

Rules for filling the plan:
- Each task is a **coherent unit of work** — one logical change, roughly one commit's worth. Two changes that only make sense together belong in one task. Trivially small standalone changes (1-2 lines) should merge into a related task.
- **Acceptance criteria must be verifiable by running something** — not "works correctly," but "`GET /api/orders?from=2025-01-01` returns 200 with array of OrderSchema entries where `created_at >= 2025-01-01`" or "`npm test src/foo.spec.ts` passes after the change"
- **Files list must be concrete paths** (from Step 3 exploration)
- **Description: WHAT and WHY, not HOW for internals** — leave private implementation choices to the executor
- **Approach:** ONE sentence stating the overall strategy
- **Plan name:** kebab-case (used for directory naming)
- **Out of scope:** explicit boundary so the executor doesn't drift
- **Risks:** initial list — Step 5's premortem may add more

**Now output the plan in this exact markdown structure:**

```markdown
# Plan: [Plan Name]

**Created:** {YYYY-MM-DD}
**Status:** draft

## Scope

**In scope:**
- [confirmed requirement 1 from Step 2]
- [confirmed requirement 2]

**Out of scope:**
- [explicit exclusion 1]
- [explicit exclusion 2]

## Approach

[1-sentence strategy]

## Component Notes

- `path/to/file.ts`: [hidden behavior or constraint that affects the plan]
- `path/to/other.ts`: [another finding]

## Tasks

### Task 1: [Name]
- **Files:** `path/one.ts`, `path/two.ts`
- **Description:** [what to do — WHAT and WHY, not HOW for internals]
- **Acceptance:** [verifiable check]

### Task 2: [Name]
- **Files:** `path/three.ts`
- **Description:** [...]
- **Acceptance:** [...]

## Risks

- [risk] — [1-line mitigation]

OR if no real risks:

- None — routine work
```

## Step 5: Feasibility Walkthrough

Before presenting to the user, validate the plan by simulating its completion. Step 4 said WHAT the plan is; this step asks WHETHER it would actually work.

Rules:
- **Anchor every claim in a concrete plan element.** Cite task name, file, or a specific finding from Step 3. Do not invent risks; cite their source.
- **"Satisfied"** requires naming the artifact (output, behavior, file, endpoint) that fulfills the requirement once all tasks complete.
- **"Gap"** requires naming the specific missing capability or assumption that fails.
- **Premortem failure modes must be specific and cited.** "Export endpoint times out on large date ranges because Task 2 doesn't paginate (constraint from `src/api/export.ts` Component Note)" is good. "The executor might miss something" is not.

**Now output both tables:**

**Requirement Satisfaction Trace:**
| Requirement (from Step 2) | Tasks That Satisfy It | Artifact After Plan Completes | Verdict |
|---------------------------|----------------------|------------------------------|---------|
| [confirmed requirement] | Task 1, Task 3 | [concrete output, e.g., "GET /api/reports endpoint returning streamed CSV"] | SATISFIED / GAP: [what's missing] |

**Premortem — 3 most likely failure modes:**
| # | Failure Mode | Source in the Plan | Mitigation |
|---|--------------|--------------------|------------|
| 1 | [specific failure] | [task / file / Step 3 finding / requirement detail that creates the risk] | [plan change, OR "ACCEPTED RISK: [rationale]"] |
| 2 | ... | ... | ... |
| 3 | ... | ... | ... |

Resolution:
- For any **GAP** verdict: revise the task list in Step 4 before proceeding. Re-run the affected trace row after revision.
- For each premortem row: either apply the mitigation to the plan (revise a task, add a risk to the Risks section with the mitigation, or change the approach), or mark "ACCEPTED RISK" with a rationale the user can weigh in Step 6.
- Update the **Risks** section of the plan markdown to reflect any premortem-derived items.

## Step 6: User Checkpoint

Present BOTH artifacts to the user:
1. The full markdown plan from Step 4 (with Risks section now reflecting Step 5 findings)
2. The Step 5 feasibility walkthrough (trace table + premortem table)

Then ask: "Approve to write the plan file, or tell me what to change?"

If user wants changes:
- Apply them inline (edit the markdown plan and/or revise the feasibility output)
- Re-show the updated plan + walkthrough
- Repeat until approved

If user rejects an "ACCEPTED RISK" rationale: revise the plan to address it, re-run Step 5 for the affected row, and re-present.

If user approves: proceed to Step 7.

The user is the only review this skill has. The user is the quality gate.

## Step 7: Write Plan File

Write the approved plan to disk.

1. Create directory: `.workflow/plans/{YYMMDD}-{slug}/`
   - `{YYMMDD}` = today's date (e.g., `260512`)
   - `{slug}` = kebab-case from plan name
2. Write `plan.md` with the approved content from Step 4 (including the final Risks section that incorporates Step 5 findings). Update the header from `**Status:** draft` to `**Status:** approved`.
3. Tell the user: "Plan saved at `.workflow/plans/{YYMMDD}-{slug}/plan.md`."

The Step 5 feasibility walkthrough tables remain in the conversation log but are not persisted into `plan.md` — they were a validation artifact, not part of the executable plan.

## Questions This Skill Answers

- "/plan-quick [requirement]"
- "Simple plan for [X]"
- "Lightweight plan, no JSON"
- "Markdown plan for [requirement]"
- "Plan from gh:123 simply"
- "Plan from jira:PROJ-X without the full review process"
- "I want a plan I can edit by hand"
