---
description: "Fetch a GitLab issue or work item as clean markdown for planning"
---

# /gitlab — Fetch GitLab Issue / Work Item

Fetch a GitLab issue or work item and present it as clean markdown for `/plan` input.

**Input:** `/gitlab 123`, `/gitlab owner/repo#123`, or `/gitlab {url}`
**Output:** Clean markdown printed to the conversation

## Process

1. Read `.workflow/config.json` to get GitLab settings:
   - `gitlab.base_url` — e.g., `https://gitlab.com`
   - `gitlab.token` — Personal Access Token (direct value), or `gitlab.auth_env_var` — env var name (default: `GITLAB_TOKEN`)
   - `gitlab.default_project` — used if only a number is given (e.g., `998-V2/documents`)

2. Run the fetch script:
   ```
   python .claude/scripts/gitlab_fetch.py {input} [--scope issue|all] [--comments N] [--no-download]
   ```

   **Options:**
   - `--scope issue` — fetch description only (no comments)
   - `--scope all` — fetch description + comments (default)
   - `--comments N` — max comments when scope=all (default: 10)
   - `--no-download` — skip downloading attachments, keep remote URLs
   - `--output-dir DIR` — save output to custom directory (default: `.workflow/`)

   The script auto-detects the input type:
   - `123` or `#123` → uses `default_project` from config, fetches as issue
   - `owner/repo#123` → fetches as issue
   - URL with `/issues/` → fetches as issue via REST API
   - URL with `/work_items/` → fetches as work item via GraphQL API

3. The script:
   - Outputs clean markdown to stdout
   - Downloads images to `{output_dir}/images/` and file attachments to `{output_dir}/files/`
   - Rewrites attachment paths to local paths so the AI agent can read them
   - Appends an **Attachments** manifest table at the end listing all downloaded files
   - Saves the markdown to `{output_dir}/gitlab-{number}.md`

4. Present the output to the user or return it to the calling skill.

## Setup

Requires `.workflow/config.json` with GitLab settings:
```json
{
  "gitlab": {
    "base_url": "https://gitlab.com",
    "token": "glpat-...",
    "default_project": "998-V2/documents"
  }
}
```

Alternatively, set `auth_env_var` instead of `token` to read from an environment variable.

## Constraints
- Do NOT make direct API calls in-context — the script handles this to avoid token waste
- Do NOT include system notes (label changes, assignments, milestone updates) in output
- Strip any HTML in the body if present
- Maximum 10 comments/notes by default
