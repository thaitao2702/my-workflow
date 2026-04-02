---
description: "Fetch and transform a Jira ticket into clean markdown for planning"
---

# /jira — Fetch Jira Ticket

Fetch a Jira ticket and transform its content (ADF format) into clean, AI-friendly markdown.

**Input:** `/jira PROJ-456` or `/jira {ticket-id}`
**Output:** Clean markdown printed to the conversation (consumed by `/plan` or user)

## Process

1. Read `.workflow/config.json` to get Jira settings:
   - `jira.base_url` — e.g., `https://yourorg.atlassian.net`
   - `jira.auth_env_var` — environment variable name containing the API token (default: `JIRA_TOKEN`)
   - `jira.default_project` — used if ticket ID has no project prefix

2. Run the fetch script:
   ```
   python .claude/scripts/jira_fetch.py {ticket-id}
   ```

3. The script outputs clean markdown to stdout. Present it to the user or return it to the calling skill.

## Setup

Requires `.workflow/config.json` with Jira settings:
```json
{
  "jira": {
    "base_url": "https://yourorg.atlassian.net",
    "auth_env_var": "JIRA_TOKEN",
    "email_env_var": "JIRA_EMAIL",
    "default_project": "PROJ"
  }
}
```

Environment variables `JIRA_EMAIL` and `JIRA_TOKEN` must be set.

## Constraints
- Do NOT make direct API calls in-context — the script handles this to avoid token waste
- Do NOT include Jira metadata noise (reporter, watchers, workflow transitions) in output
- The script strips HTML, transforms ADF to markdown, and keeps only useful content
