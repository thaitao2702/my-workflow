#!/usr/bin/env python3
"""Fetch a GitLab issue or work item and output clean markdown.

Usage:
    python .claude/scripts/gitlab_fetch.py 9595
    python .claude/scripts/gitlab_fetch.py 998-V2/documents#9595
    python .claude/scripts/gitlab_fetch.py https://gitlab.com/998-V2/documents/-/work_items/9595
    python .claude/scripts/gitlab_fetch.py https://gitlab.com/998-V2/documents/-/issues/42
    python .claude/scripts/gitlab_fetch.py 9595 --scope issue
    python .claude/scripts/gitlab_fetch.py 9595 --scope all --comments 10

Reads GitLab config from .workflow/config.json:
    {
        "gitlab": {
            "base_url": "https://gitlab.com",
            "token": "glpat-...",
            "default_project": "998-V2/documents"
        }
    }

Auth: Personal Access Token with read_api scope.
      Set gitlab.token in config or GITLAB_TOKEN env var.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path


# ---------------------------------------------------------------------------
# Project root & config
# ---------------------------------------------------------------------------

def find_project_root() -> Path:
    """Walk up from script location to find .workflow/ directory."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / ".workflow").is_dir() or (current / ".claude").is_dir():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    print("Error: Could not find project root (.workflow/ or .claude/ directory)", file=sys.stderr)
    sys.exit(1)


def load_config(root: Path) -> dict:
    """Load GitLab config from .workflow/config.json."""
    config_path = root / ".workflow" / "config.json"
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        print("Create .workflow/config.json with gitlab.base_url, gitlab.token", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    gitlab = config.get("gitlab")
    if not gitlab:
        print("Error: No 'gitlab' section in .workflow/config.json", file=sys.stderr)
        sys.exit(1)

    if not gitlab.get("base_url"):
        print("Error: gitlab.base_url is required in .workflow/config.json", file=sys.stderr)
        sys.exit(1)

    return gitlab


# ---------------------------------------------------------------------------
# Input parsing
# ---------------------------------------------------------------------------

def parse_input(raw: str, config: dict) -> tuple[str, str, str]:
    """Parse user input into (project_path, number, item_type).

    item_type is 'issue' or 'work_item'.
    """
    # Full URL: https://gitlab.com/group/project/-/issues/123
    #           https://gitlab.com/group/project/-/work_items/123
    url_match = re.match(
        r"https?://[^/]+/(.+?)/-/(issues|work_items)/(\d+)",
        raw,
    )
    if url_match:
        project_path = url_match.group(1)
        item_type = "work_item" if url_match.group(2) == "work_items" else "issue"
        number = url_match.group(3)
        return project_path, number, item_type

    # owner/repo#123
    ref_match = re.match(r"^(.+?)#(\d+)$", raw)
    if ref_match:
        return ref_match.group(1), ref_match.group(2), "issue"

    # Plain number: 123 or #123
    num_match = re.match(r"^#?(\d+)$", raw)
    if num_match:
        default_project = config.get("default_project")
        if not default_project:
            print(
                f"Error: Numeric ID '{raw}' requires gitlab.default_project in config",
                file=sys.stderr,
            )
            sys.exit(1)
        return default_project, num_match.group(1), "issue"

    print(f"Error: Could not parse input: '{raw}'", file=sys.stderr)
    print("Expected: 123, owner/repo#123, or a full GitLab URL", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def api_get(url: str, token: str) -> dict:
    """GET request to GitLab REST API."""
    req = urllib.request.Request(url)
    req.add_header("PRIVATE-TOKEN", token)
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: Not found — {url}", file=sys.stderr)
        elif e.code == 401:
            print("Error: Authentication failed. Check GITLAB_TOKEN.", file=sys.stderr)
        elif e.code == 403:
            print("Error: Permission denied.", file=sys.stderr)
        else:
            print(f"Error: GitLab API returned {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to GitLab: {e.reason}", file=sys.stderr)
        sys.exit(1)


def graphql_query(base_url: str, token: str, query: str) -> dict:
    """POST a GraphQL query to GitLab."""
    url = f"{base_url.rstrip('/')}/api/graphql"
    payload = json.dumps({"query": query}).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("Error: Authentication failed. Check GITLAB_TOKEN.", file=sys.stderr)
        else:
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            print(f"Error: GraphQL returned {e.code}: {body[:500]}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to GitLab: {e.reason}", file=sys.stderr)
        sys.exit(1)

    if "errors" in data and data["errors"]:
        msgs = "; ".join(e.get("message", str(e)) for e in data["errors"])
        print(f"Error: GraphQL errors — {msgs}", file=sys.stderr)
        sys.exit(1)

    return data


# ---------------------------------------------------------------------------
# Fetch: Issue (REST)
# ---------------------------------------------------------------------------

def fetch_issue(base_url: str, project_path: str, number: str, token: str, max_comments: int) -> str:
    """Fetch a GitLab issue via REST API and return markdown."""
    encoded_project = urllib.parse.quote(project_path, safe="")
    api_base = f"{base_url.rstrip('/')}/api/v4/projects/{encoded_project}"

    # Fetch issue
    issue = api_get(f"{api_base}/issues/{number}", token)

    title = issue.get("title", "Untitled")
    state = issue.get("state", "unknown")
    labels = ", ".join(issue.get("labels", [])) or "None"
    assignees = ", ".join(a.get("name", a.get("username", "")) for a in issue.get("assignees", [])) or "None"
    description = issue.get("description") or ""

    lines = [
        f"# #{number}: {title}",
        "",
        f"**Status:** {state} | **Labels:** {labels} | **Assignees:** {assignees}",
        "",
    ]

    if description:
        lines.append("## Description")
        lines.append("")
        lines.append(resolve_upload_urls(convert_html(description), base_url, project_path).strip())
        lines.append("")

    # Fetch notes (comments) — skip if max_comments == 0
    if max_comments > 0:
        notes_url = f"{api_base}/issues/{number}/notes?sort=asc&per_page={max_comments}"
        try:
            notes = api_get(notes_url, token)
        except SystemExit:
            notes = []

        user_notes = [n for n in notes if not n.get("system", False)]
        if user_notes:
            lines.append("## Comments")
            lines.append("")
            for note in user_notes[:max_comments]:
                author = note.get("author", {}).get("name", "Unknown")
                created = note.get("created_at", "")[:10]
                body = resolve_upload_urls(convert_html(note.get("body", "")), base_url, project_path).strip()
                lines.append(f"**{author}** ({created}):")
                lines.append("")
                lines.append(body)
                lines.append("")
                lines.append("---")
                lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Fetch: Work Item (GraphQL)
# ---------------------------------------------------------------------------

WORK_ITEM_QUERY_WITH_NOTES = """
query {{
  project(fullPath: "{project_path}") {{
    workItems(iids: ["{number}"], first: 1) {{
      nodes {{
        title
        state
        description
        widgets {{
          type
          ... on WorkItemWidgetNotes {{
            discussions(first: {max_discussions}) {{
              nodes {{
                notes(first: 5) {{
                  nodes {{
                    body
                    system
                    author {{
                      name
                    }}
                    createdAt
                  }}
                }}
              }}
            }}
          }}
          ... on WorkItemWidgetLabels {{
            labels {{
              nodes {{
                title
              }}
            }}
          }}
          ... on WorkItemWidgetAssignees {{
            assignees {{
              nodes {{
                name
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""

WORK_ITEM_QUERY_NO_NOTES = """
query {{
  project(fullPath: "{project_path}") {{
    workItems(iids: ["{number}"], first: 1) {{
      nodes {{
        title
        state
        description
        widgets {{
          type
          ... on WorkItemWidgetLabels {{
            labels {{
              nodes {{
                title
              }}
            }}
          }}
          ... on WorkItemWidgetAssignees {{
            assignees {{
              nodes {{
                name
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}
"""


def fetch_work_item(base_url: str, project_path: str, number: str, token: str, max_comments: int) -> str:
    """Fetch a GitLab work item via GraphQL API and return markdown."""
    if max_comments > 0:
        query = WORK_ITEM_QUERY_WITH_NOTES.format(
            project_path=project_path,
            number=number,
            max_discussions=max_comments,
        )
    else:
        query = WORK_ITEM_QUERY_NO_NOTES.format(
            project_path=project_path,
            number=number,
        )
    data = graphql_query(base_url, token, query)

    nodes = data.get("data", {}).get("project", {}).get("workItems", {}).get("nodes", [])
    if not nodes:
        print(f"Error: Work item #{number} not found in {project_path}", file=sys.stderr)
        sys.exit(1)

    work_item = nodes[0]
    title = work_item.get("title", "Untitled")
    state = work_item.get("state", "unknown")

    # Extract from widgets
    labels = []
    assignees = []
    discussions = []

    for widget in work_item.get("widgets", []):
        wtype = widget.get("type", "")
        if wtype == "LABELS":
            labels = [n.get("title", "") for n in widget.get("labels", {}).get("nodes", [])]
        elif wtype == "ASSIGNEES":
            assignees = [n.get("name", "") for n in widget.get("assignees", {}).get("nodes", [])]
        elif wtype == "NOTES" and max_comments > 0:
            for disc in widget.get("discussions", {}).get("nodes", []):
                for note in disc.get("notes", {}).get("nodes", []):
                    if not note.get("system", False):
                        discussions.append(note)

    labels_str = ", ".join(labels) or "None"
    assignees_str = ", ".join(assignees) or "None"
    description = work_item.get("description") or ""

    lines = [
        f"# #{number}: {title}",
        "",
        f"**Status:** {state} | **Labels:** {labels_str} | **Assignees:** {assignees_str}",
        "",
    ]

    if description:
        lines.append("## Description")
        lines.append("")
        lines.append(resolve_upload_urls(convert_html(description), base_url, project_path).strip())
        lines.append("")

    if discussions:
        lines.append("## Comments")
        lines.append("")
        for note in discussions[:max_comments]:
            author = note.get("author", {}).get("name", "Unknown")
            created = note.get("createdAt", "")[:10]
            body = resolve_upload_urls(convert_html(note.get("body", "")), base_url, project_path).strip()
            lines.append(f"**{author}** ({created}):")
            lines.append("")
            lines.append(body)
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

class _HTMLTableParser(HTMLParser):
    """Parse HTML tables into markdown tables. Pass through non-table content."""

    def __init__(self):
        super().__init__()
        self._in_table = False
        self._in_row = False
        self._in_cell = False
        self._rows: list[list[str]] = []
        self._current_row: list[str] = []
        self._current_cell: list[str] = []
        self._output: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self._in_table = True
            self._rows = []
        elif tag == "tr":
            self._in_row = True
            self._current_row = []
        elif tag in ("td", "th"):
            self._in_cell = True
            self._current_cell = []
        elif tag == "br" and self._in_cell:
            self._current_cell.append(" ")

    def handle_endtag(self, tag):
        if tag in ("td", "th"):
            self._current_row.append("".join(self._current_cell).strip())
            self._current_cell = []
            self._in_cell = False
        elif tag == "tr":
            if self._current_row:
                self._rows.append(self._current_row)
            self._current_row = []
            self._in_row = False
        elif tag == "table":
            self._flush_table()
            self._in_table = False

    def handle_data(self, data):
        if self._in_cell:
            self._current_cell.append(data)
        elif not self._in_table:
            self._output.append(data)

    def _flush_table(self):
        if not self._rows:
            return
        col_count = max(len(r) for r in self._rows)
        # Pad rows
        for row in self._rows:
            while len(row) < col_count:
                row.append("")
        # Build markdown table as a single block with newlines
        lines = []
        header = self._rows[0]
        lines.append("| " + " | ".join(h.replace("\n", " ") for h in header) + " |")
        lines.append("| " + " | ".join(["---"] * col_count) + " |")
        for row in self._rows[1:]:
            cells = [c.replace("\n", " ").replace("|", "\\|") for c in row]
            lines.append("| " + " | ".join(cells) + " |")
        self._output.append("\n" + "\n".join(lines) + "\n")

    def get_output(self) -> str:
        return "".join(self._output)


def convert_html(text: str) -> str:
    """Convert HTML tables to markdown tables, strip remaining HTML tags."""
    if not text:
        return ""
    # Only invoke parser if there are HTML tables
    if "<table" in text.lower():
        parser = _HTMLTableParser()
        parser.feed(text)
        text = parser.get_output()
    # Strip any remaining HTML tags
    return re.sub(r"<[^>]+>", "", text)


def resolve_upload_urls(text: str, base_url: str, project_path: str) -> str:
    """Rewrite relative /uploads/ paths to absolute GitLab URLs."""
    if not text:
        return ""
    return re.sub(
        r"(\(/uploads/)",
        f"({base_url.rstrip('/')}/{project_path}/uploads/",
        text,
    )


def download_attachments(
    text: str,
    token: str,
    base_url: str,
    project_path: str,
    output_dir: Path,
) -> str:
    """Download all attachments (images + files) from markdown, rewrite paths.

    Returns the rewritten markdown text and appends an Attachments manifest.
    """
    encoded_project = urllib.parse.quote(project_path, safe="")
    img_dir = output_dir / "images"
    file_dir = output_dir / "files"
    manifest: list[tuple[str, str, str]] = []  # (type, filename, local_path)

    def _to_api_url(url: str) -> str:
        """Convert a GitLab upload URL to the API endpoint that serves it."""
        m = re.search(r"/uploads/([a-f0-9]+/.+)$", url)
        if m:
            return f"{base_url.rstrip('/')}/api/v4/projects/{encoded_project}/uploads/{m.group(1)}"
        return url

    def _download(url: str, dest: Path) -> bool:
        """Download a URL to a local path. Returns True on success."""
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            api_url = _to_api_url(url)
            req = urllib.request.Request(api_url)
            req.add_header("PRIVATE-TOKEN", token)
            with urllib.request.urlopen(req, timeout=15) as resp:
                dest.write_bytes(resp.read())
            return True
        except Exception:
            return False

    def _local_filename(url: str) -> str:
        """Derive a local filename from a GitLab upload URL."""
        if "/uploads/" in url:
            return url.split("/uploads/")[-1].replace("/", "_")
        return url.split("/")[-1]

    # Pass 1: Images — ![alt](url){attributes}
    def _replace_image(match):
        alt = match.group(1)
        url = match.group(2)
        # group(3) captures optional {width=...} attributes — drop them for local paths

        if not url.startswith("http"):
            return match.group(0)

        filename = _local_filename(url)
        local_path = img_dir / filename

        if _download(url, local_path):
            manifest.append(("image", filename, local_path.as_posix()))
            return f"![{alt}]({local_path.as_posix()})"
        return match.group(0)

    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)(\{[^}]*\})?", _replace_image, text)

    # Pass 2: File links — [text](url) where url contains /uploads/ (but NOT images)
    def _replace_file(match):
        link_text = match.group(1)
        url = match.group(2)

        if not url.startswith("http") or "/uploads/" not in url:
            return match.group(0)

        filename = _local_filename(url)
        local_path = file_dir / filename

        if _download(url, local_path):
            manifest.append(("file", filename, local_path.as_posix()))
            return f"[{link_text}]({local_path.as_posix()})"
        return match.group(0)

    text = re.sub(r"(?<!!)\[([^\]]*)\]\((https?://[^)]+/uploads/[^)]+)\)", _replace_file, text)

    # Append manifest if any attachments were downloaded
    if manifest:
        text = text.rstrip() + "\n\n"
        text += "## Attachments\n\n"
        text += "| Type | File | Local Path |\n"
        text += "| --- | --- | --- |\n"
        for atype, fname, lpath in manifest:
            text += f"| {atype} | {fname} | {lpath} |\n"

    return text


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch a GitLab issue or work item and output clean markdown.",
        usage="python .claude/scripts/gitlab_fetch.py <input> [--scope issue|all] [--comments N]",
    )
    parser.add_argument(
        "input",
        help="Issue/work item reference: 123, owner/repo#123, or full GitLab URL",
    )
    parser.add_argument(
        "--scope",
        choices=["issue", "all"],
        default="all",
        help="Fetch scope: 'issue' = description only, 'all' = description + comments (default: all)",
    )
    parser.add_argument(
        "--comments",
        type=int,
        default=10,
        help="Max comments to include when --scope=all (default: 10)",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Directory to save output file and attachments (default: .workflow/)",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip downloading attachments (keep remote URLs)",
    )
    args = parser.parse_args()

    root = find_project_root()
    config = load_config(root)

    project_path, number, item_type = parse_input(args.input, config)

    # Resolve token: direct "token" field first, then env var via "auth_env_var"
    token = config.get("token")
    if not token:
        token_var = config.get("auth_env_var", "GITLAB_TOKEN")
        token = os.environ.get(token_var)
    if not token:
        print("Error: No GitLab token found.", file=sys.stderr)
        print("Set gitlab.token in .workflow/config.json or set the GITLAB_TOKEN env var.", file=sys.stderr)
        print("Create a Personal Access Token with read_api scope at:", file=sys.stderr)
        print(f"  {config['base_url']}/-/user_settings/personal_access_tokens", file=sys.stderr)
        sys.exit(1)

    base_url = config["base_url"]

    # Determine comment count based on scope
    max_comments = args.comments if args.scope == "all" else 0

    # Fetch based on type
    if item_type == "work_item":
        output = fetch_work_item(base_url, project_path, number, token, max_comments)
    else:
        output = fetch_issue(base_url, project_path, number, token, max_comments)

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else root / ".workflow"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Download attachments unless --no-download
    if not args.no_download:
        output = download_attachments(output, token, base_url, project_path, output_dir)

    # Save to file and print to stdout
    slug = f"gitlab-{number}"
    out_file = output_dir / f"{slug}.md"
    out_file.write_bytes(output.encode("utf-8"))
    print(f"Saved to {out_file}", file=sys.stderr)

    sys.stdout.buffer.write(output.encode("utf-8"))


if __name__ == "__main__":
    main()
