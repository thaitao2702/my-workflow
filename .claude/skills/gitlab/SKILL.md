---
description: "Fetch a GitLab issue as clean markdown for planning"
---

# /gitlab — Fetch GitLab Issue

Fetch a GitLab issue and present it as clean markdown for `/plan` input.

**Input:** `/gitlab 123`, `/gitlab owner/repo#123`, or `/gitlab {url}`
**Output:** Clean markdown printed to the conversation

## Process

1. Parse the input:
   - `123` or `#123` → current project, issue 123
   - `owner/repo#123` → specific project
   - Full GitLab URL → extract owner/repo/number

2. Fetch using GitLab CLI:
   ```
   glab issue view {number} -R {owner/repo}
   ```
   If no `-R` needed (current project), omit it. Use `--json` flags if available in installed `glab` version for structured output.

3. Format output:

   ```markdown
   # #{number}: {title}

   **Status:** {state} | **Labels:** {labels} | **Assignees:** {assignees}

   ## Description
   {body — already markdown, pass through}

   ## Comments
   {latest 10 comments/notes, each with author + date + body}
   ```

4. Present to user or return to calling skill.

## Requirements
- `glab` CLI must be installed and authenticated (`glab auth status`)
- If not available, inform the user and ask them to paste issue content directly

## Constraints
- Do NOT fetch more than 10 comments/notes
- Do NOT include system notes (label changes, assignments, milestone updates)
- Strip any HTML in the body if present
