# Function 5: Template (`/template`)

## Purpose

Extract repeatable implementation patterns from completed work into reusable templates. When a feature is built that will repeat with variations (new payment vendors, CRUD pages, API integrations), `/template create` captures the pattern — steps, files, integration points, and what varies vs what stays fixed. `/template apply` then uses that template to accelerate future instances, feeding into `/plan` or `/execute`.

## When to Run

| Trigger | Mode | Example |
|---------|------|---------|
| User just built something repeatable | `create` | "I just integrated Stripe, more providers are coming" |
| User wants to template an existing module | `create` | "Template our table page pattern from the Reports page" |
| User wants to build the next instance | `apply` | "Add PayPal using the payment-provider template" |
| `/plan` detects a matching template | `apply` (auto-suggested) | Planning sees "add payment vendor" and finds existing template |

## The Variability Problem

Not all templates are the same level of cookie-cutter. A table page is 90% identical each time. A payment vendor UI varies wildly. The template format must handle this spectrum without forcing everything into one mold.

### Three Variability Levels (per section, not per template)

Each section/step in a template declares its own variability:

| Level | Marker | Meaning | Example |
|-------|--------|---------|---------|
| **FIXED** | `[F]` | Copy as-is every time. Structure, logic, and code are identical. | Error handling wrapper, retry config shape, table shell component |
| **PARAMETRIC** | `[P]` | Same structure, swap clearly-defined values. Fill-in-the-blanks. | Column definitions, API endpoint paths, config keys, provider name |
| **GUIDED** | `[G]` | Follow the general pattern but expect structural differences. AI must reason. | Payment vendor UI (fields vary per vendor), custom validation logic |

**Why per-section, not per-template:** A single template has sections at different variability levels. The Stripe integration template: config registration is `[F]`, client class is `[P]`, admin UI is `[G]`. Marking the whole template as one level loses this nuance.

**How this helps the AI:**
- `[F]` sections: copy reference, change nothing structural
- `[P]` sections: find the variables, ask user for values, substitute
- `[G]` sections: read the reference for shape/intent, but plan the implementation with user input

## Storage

```
.workflow/templates/
├── index.md                        ← Master index (referenced by CLAUDE.md)
└── {template-name}/
    ├── template.md                 ← The playbook
    └── references/                 ← Snapshots of key files from the original
        ├── {file1-slug}.md         ← File content + annotations
        └── {file2-slug}.md
```

### Template Index (`.workflow/templates/index.md`)

```markdown
# Integration Templates

| Template | Pattern | Trigger Keywords | Created From |
|----------|---------|-----------------|--------------|
| payment-provider | Third-party payment gateway integration | payment, gateway, provider, vendor | Stripe integration (2026-03-22) |
| crud-table-page | Standard data table with filters and CRUD | table, list, grid, data page | Reports page (2026-03-20) |
| api-resource | REST API resource endpoint set | endpoint, api, resource, CRUD API | /api/reports (2026-03-18) |
```

**Why an index with trigger keywords:** When `/plan` receives a requirement like "add PayPal payment support," the orchestrator scans this index. Keywords `payment` + `provider` match → suggest the template to the user. No manual lookup needed.

### CLAUDE.md Addition

```markdown
## Integration Templates
Template index: `.workflow/templates/index.md`
When planning new features, check if an existing template matches before planning from scratch.
Templates capture repeatable patterns — use `/template apply {name}` to accelerate implementation.
```

## Template File Format: `template.md`

```markdown
---
name: {template-name}
description: {one-line description}
created_from: {source — git range, component path, or description}
created_at: {ISO date}
trigger_keywords: [keyword1, keyword2, keyword3]
variables:
  - name: {variable_name}
    description: {what this variable represents}
    example: {example value from original implementation}
  - name: {variable_name_2}
    description: {what this variable represents}
    example: {example value}
---

# {Template Name}

## Overview
{1-2 sentence description of what this pattern does and when to use it}

## Variables
| Variable | Description | Example (from original) |
|----------|-------------|------------------------|
| `{provider_name}` | The payment provider identifier | `stripe` |
| `{api_base_url}` | Provider's API base URL | `https://api.stripe.com/v1` |
| `{auth_method}` | How the provider authenticates | `bearer_token` |

## Steps

### Step 1: {step-name} [P]
**Files:** `src/services/{provider_name}Client.ts` (create)
**Reference:** [references/stripe-client.md](references/stripe-client.md)
**What to do:**
- Create provider client class following the reference structure
- Implement methods: `charge()`, `refund()`, `getStatus()`
- Variable parts: API endpoints, request/response shapes
- Fixed parts: retry logic, error wrapping, logging pattern

### Step 2: {step-name} [F]
**Files:** `src/config/providers.ts` (modify — add entry)
**Reference:** [references/provider-registry.md](references/provider-registry.md)
**What to do:**
- Add new provider to the `PROVIDERS` enum
- Add config entry to `PROVIDER_CONFIG` map
- This is identical every time — just a new key-value pair

### Step 3: {step-name} [G]
**Files:** `src/pages/admin/providers/{provider_name}/Settings.tsx` (create)
**Reference:** [references/stripe-settings-page.md](references/stripe-settings-page.md)
**What to do:**
- Create settings page for the new provider
- Follow the general layout pattern (header, form, save action)
- **Expect variation:** form fields depend entirely on what the provider needs
- User must specify: what fields this provider requires, validation rules
- Reference shows Stripe's version — use as structural guide, not exact copy

## Integration Points
{Where the new code connects to existing code — critical for AI to know what to modify}

| Integration Point | File | Action | Level |
|-------------------|------|--------|-------|
| Provider registry | `src/config/providers.ts` | Add enum + config entry | [F] |
| Route mapping | `src/routes/admin.ts` | Add route for settings page | [P] |
| Navigation menu | `src/components/AdminNav.tsx` | Add menu item | [P] |
| Payment processor | `src/services/paymentProcessor.ts` | Add case to switch | [F] |

## Tests Required
| Test | File Pattern | Level | Notes |
|------|-------------|-------|-------|
| Client unit tests | `src/services/__tests__/{provider_name}Client.test.ts` | [P] | Same test structure, different API mocks |
| Integration test | `src/tests/integration/payment-{provider_name}.test.ts` | [G] | Depends on provider's test/sandbox API |
| Settings page test | `src/pages/admin/providers/{provider_name}/__tests__/Settings.test.tsx` | [G] | Varies with form fields |

## Gotchas & Lessons Learned
{Non-obvious things discovered during the original implementation — saves hours}

- {gotcha 1: e.g., "Provider X returns 200 even on errors — must check response body"}
- {gotcha 2: e.g., "Admin settings page must call `invalidateCache('providers')` after save"}
- {gotcha 3: e.g., "Webhook endpoint must be registered in provider dashboard before testing"}
```

### Reference File Format

Reference files are **annotated snapshots** of the original implementation — not raw code dumps. They highlight what matters.

```markdown
---
source: src/services/stripeClient.ts
snapshot_commit: abc123f
---

# StripeClient — Reference for Payment Provider Template

## Key Structure
{Annotated code showing the pattern. Comments mark FIXED vs PARAMETRIC vs GUIDED sections.}

​```typescript
// [F] — Base class structure is always the same
export class StripeClient extends BasePaymentClient {
  // [P] — Constructor takes provider-specific config
  constructor(config: StripeConfig) {
    super(config.apiKey, config.baseUrl);
  }

  // [P] — Method signature is the same, implementation details vary
  async charge(amount: number, currency: string, source: string): Promise<ChargeResult> {
    // [G] — Request building varies by provider API shape
    const response = await this.post('/charges', {
      amount,
      currency,
      source,
    });

    // [F] — Error wrapping is always the same
    if (!response.ok) {
      throw new PaymentError(this.provider, response.status, response.body);
    }

    // [P] — Response mapping: same shape out, different shape in
    return this.mapToChargeResult(response.body);
  }
}
​```

## What to Keep
- The `BasePaymentClient` inheritance pattern
- Error wrapping with `PaymentError`
- The `mapToChargeResult` normalization step

## What to Change
- Config type (each provider has different required fields)
- API endpoint paths and request shapes
- Response body structure and field mapping
```

## Process

### Mode 1: `/template create {name}`

```
Step 1: Gather Source Material
├── Ask user: "What work should I analyze?"
│   ├── Option A: Git range — "last 5 commits" or "abc123..def456"
│   ├── Option B: File paths — "src/services/stripeClient.ts, src/config/providers.ts, ..."
│   ├── Option C: Existing component — "the Reports table page"
│   └── Option D: Mixed — git range + user description of intent
│
├── If git range: extract changed files, read diffs
├── If file paths: read current state of those files
├── If component path: read component + its .analysis.md if exists

Step 2: Pattern Extraction (Opus agent)
├── Analyze all source material
├── Identify:
│   ├── What is the repeatable pattern? (the "shape" of the work)
│   ├── What are the steps? (ordered sequence of file operations)
│   ├── What varies? → mark as [P] parametric or [G] guided
│   ├── What stays the same? → mark as [F] fixed
│   ├── What are the variables? (names, values that change each time)
│   ├── What are the integration points? (where new code touches existing code)
│   ├── What tests follow the pattern?
│   └── What gotchas/non-obvious behaviors exist?
│
├── Generate template.md with full structure
├── Generate reference files for key source files (annotated snapshots)

Step 3: User Review
├── Present the template to user
├── User can:
│   ├── Adjust variability levels (promote [P] to [G] or demote to [F])
│   ├── Add/remove variables
│   ├── Add gotchas the AI missed
│   ├── Refine step descriptions
│   └── Approve
│
└── Write to .workflow/templates/{name}/
    ├── Update index.md with new entry
    └── Update CLAUDE.md if first template (add Templates section)
```

### Mode 2: `/template apply {name}`

```
Step 1: Load Template
├── Read .workflow/templates/{name}/template.md
├── Read reference files
├── Present template overview to user

Step 2: Collect Variables
├── For each variable defined in template:
│   ├── Show: variable name, description, example from original
│   └── Ask user for value
│
├── For [G] guided sections:
│   ├── Show: what the original did and why
│   └── Ask user: "How should this differ for your case?"
│       (e.g., "What fields does PayPal require on the settings page?")

Step 3: Generate Output
├── User chooses output mode:
│   ├── "Plan" → generate a /plan-compatible plan.md
│   │   ├── Template steps become plan phases/tasks
│   │   ├── [F] and [P] sections become concrete tasks with little ambiguity
│   │   ├── [G] sections become tasks with user-provided details + reference
│   │   └── Feed into /execute for implementation
│   │
│   └── "Execute directly" → generate /execute-compatible task list
│       ├── Only appropriate when ALL sections are [F] or [P] (no [G])
│       ├── If [G] sections exist, warn user: "This template has guided
│       │   sections that need planning. Recommend going through /plan first."
│       └── If user insists: proceed but flag [G] sections for human review
│
└── Hand off to /plan or /execute with template context attached
```

## How `/plan` Auto-Discovers Templates

When `/plan` receives requirements, the orchestrator does this **before** dispatching to the planner agent:

```
Planning orchestrator receives requirements
├── Read .workflow/templates/index.md
├── Match requirements text against trigger_keywords
│   ├── Simple keyword overlap scoring
│   └── Threshold: 2+ keyword matches = suggest
│
├── If match found:
│   ├── Tell user: "Found matching template: {name} — {description}"
│   ├── Ask: "Use this template as a starting point?"
│   │   ├── Yes → load template, run /template apply flow, then plan
│   │   ├── No → plan from scratch as normal
│   │   └── "Show me" → display template overview, then decide
│
└── If no match: proceed with normal planning flow
```

**Why keyword matching, not semantic search:** Keeps it simple, deterministic, and zero-cost. The trigger keywords are human-curated during template creation. If this proves too limited, can upgrade later — but don't over-engineer the matching when a dozen curated keywords per template will cover 95% of cases.

## Agent Definition

| Agent | Purpose | Model | Context Receives |
|-------|---------|-------|-----------------|
| **template-extractor** | Analyzes source material, identifies pattern, generates template | opus | Source files/diffs, project-overview, .analysis.md files for involved components |
| **template-applier** | Fills template variables, generates plan/task list | sonnet | Template + references, user-provided variable values, project-overview |

**Why Opus for extraction:** Pattern extraction is a judgment-heavy task — identifying what's truly fixed vs parametric vs guided requires understanding intent, not just diffing code. This is a one-time cost per template.

**Why Sonnet for application:** Applying a template is mostly mechanical — substitute variables, generate a plan from a known structure. Sonnet handles this efficiently.

## Design Decisions

### Decision: Per-section variability levels, not per-template
**Options considered:**
1. Mark entire template as "low/medium/high variability"
2. Mark each section/step with its own variability level

**Chose option 2.** A single template often has sections at all three levels. A payment integration: config registration is always identical (`[F]`), client class follows a clear pattern (`[P]`), but the UI varies significantly (`[G]`). Marking the whole template as "medium" loses this granularity and doesn't help the AI know which parts to copy vs reason about.

### Decision: Reference files are annotated snapshots, not raw code
**Options considered:**
1. Just copy the original files as-is
2. Annotated snapshots with [F]/[P]/[G] markers and explanatory comments

**Chose option 2.** Raw code requires the AI to re-figure-out what matters every time the template is applied. Annotations front-load that analysis once. This costs a bit more during template creation but saves tokens and reasoning on every application.

### Decision: Template index with trigger keywords for auto-discovery
**Options considered:**
1. User must explicitly invoke `/template apply {name}`
2. `/plan` auto-discovers matching templates via keyword matching
3. Semantic similarity matching against template descriptions

**Chose option 1+2.** User can always apply explicitly. But the real value is when `/plan` says "hey, there's a template for this" without the user remembering. Keyword matching is simple and sufficient — no embedding infrastructure needed. Upgrade path to semantic matching exists but isn't worth the complexity now.

### Decision: Guard rail on "execute directly" mode
**Why:** If a template has `[G]` (guided) sections, going straight to execution skips the reasoning step those sections need. The AI would be guessing at structural decisions that should involve the user. Warning + recommendation to use `/plan` first protects quality. User can override — pragmatic, not dogmatic.

### Decision: Opus for create, Sonnet for apply
**Why:** Creating a template is a one-time, high-judgment task (worth the cost). Applying a template is a recurring, lower-judgment task (optimize for cost). Same cost-aware model selection principle as the rest of the framework.

## Relationship to Other Functions

```
┌──────────────────────────────────────────────────────────────────┐
│                        Workflow Integration                      │
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌─────────┐              │
│  │ /init    │     │ /analyze     │     │ /plan   │              │
│  │          │     │              │     │         │              │
│  │ Project  │────▶│  Component   │────▶│ Plan    │              │
│  │ overview │     │  knowledge   │     │ creation│              │
│  └──────────┘     └──────────────┘     └────┬────┘              │
│                                             │                    │
│                        ┌────────────────────┤                    │
│                        │ auto-discovers     │                    │
│                        ▼                    ▼                    │
│                   ┌──────────┐        ┌──────────┐              │
│                   │/template │        │/execute  │              │
│                   │          │        │          │              │
│                   │ Pattern  │───────▶│ Execute  │              │
│                   │ reuse    │ feeds  │ tasks    │              │
│                   └──────────┘        └──────────┘              │
│                        ▲                                         │
│                        │ create from                             │
│                   completed work                                 │
│                   or existing modules                            │
└──────────────────────────────────────────────────────────────────┘
```

## Implementation Roadmap Placement

This should be **Phase 4.5** — after `/plan` (Phase 4) is built, before `/execute` (Phase 5). Reasoning:
- `/template create` needs the project context that `/init` and `/analyze` provide
- `/template apply` produces output consumed by `/plan` and `/execute`
- `/plan` needs the auto-discovery hook to suggest templates
- But `/execute` needs to understand template-generated plans (which are just regular plans)

### Items
1. **Template storage** — `.workflow/templates/` directory, index.md format
2. **CLAUDE.md integration** — Add templates section to CLAUDE.md template
3. **Template file format** — template.md schema with variability markers
4. **Reference file format** — Annotated snapshot schema
5. **Template-extractor agent** — Opus agent for pattern extraction
6. **`/template create` skill** — Orchestration: gather source → extract → user review → save
7. **Template-applier agent** — Sonnet agent for variable substitution + plan generation
8. **`/template apply` skill** — Orchestration: load → collect variables → generate plan/tasks
9. **`/plan` integration** — Auto-discovery hook: scan index, match keywords, suggest template
10. **Guard rails** — Warn on direct execution with [G] sections
