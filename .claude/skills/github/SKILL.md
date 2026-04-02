---
description: "Fetch a GitHub issue as clean markdown for planning"
---

# /github — Fetch GitHub Issue

Fetch a GitHub issue and present it as clean markdown for `/plan` input.

**Input:** `/github 123`, `/github owner/repo#123`, or `/github {url}`
**Output:** Clean markdown printed to the conversation

## Process

1. Parse the input:
   - `123` or `#123` → current repo, issue 123
   - `owner/repo#123` → specific repo
   - Full GitHub URL → extract owner/repo/number

2. Fetch using GitHub CLI:
   ```
   gh issue view {number} -R {repo} --json title,body,state,labels,comments,assignees
   ```
   If no `-R` needed (current repo), omit it.

3. Format output:

   ```markdown
   # #{number}: {title}

   **Status:** {state} | **Labels:** {labels} | **Assignees:** {assignees}

   ## Description
   {body — already markdown, pass through}

   ## Comments
   {latest 10 comments, each with author + date + body}
   ```

4. Present to user or return to calling skill.

## Requirements
- `gh` CLI must be installed and authenticated (`gh auth status`)
- If not available, inform the user and ask them to paste issue content directly

## Constraints
- Do NOT fetch more than 10 comments
- Do NOT include timeline events, reactions, or other noise
- Strip any HTML in the body (some issues mix markdown + HTML)
