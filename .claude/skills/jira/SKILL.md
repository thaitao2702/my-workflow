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
   python .claude/skills/jira/jira_fetch.py {ticket-id}
   ```

3. The script outputs clean markdown to stdout. Present it to the user or return it to the calling skill.

## If Script Doesn't Exist Yet

If `jira_fetch.py` does not exist, inform the user:
- "The Jira fetch script hasn't been set up yet. To configure:"
- "1. Set your Jira token: `export JIRA_TOKEN=your_token`"
- "2. Update `.workflow/config.json` with your Jira base URL"
- "3. The script will be created during implementation"

For now, ask the user to paste the ticket content directly.

## Constraints
- Do NOT make direct API calls in-context — the script handles this to avoid token waste
- Do NOT include Jira metadata noise (reporter, watchers, workflow transitions) in output
- The script strips HTML, transforms ADF to markdown, and keeps only useful content
