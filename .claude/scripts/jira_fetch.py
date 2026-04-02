#!/usr/bin/env python3
"""Fetch a Jira ticket and output clean markdown.

Usage:
    python .claude/scripts/jira_fetch.py PROJ-456
    python .claude/scripts/jira_fetch.py 456              # uses default_project from config
    python .claude/scripts/jira_fetch.py PROJ-456 --comments 10

Reads Jira config from .workflow/config.json:
    {
        "jira": {
            "base_url": "https://yourorg.atlassian.net",
            "auth_env_var": "JIRA_TOKEN",
            "email_env_var": "JIRA_EMAIL",
            "default_project": "PROJ"
        }
    }

Auth: Basic auth — base64(email:api_token). Set JIRA_EMAIL and JIRA_TOKEN env vars.
"""

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


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
    """Load Jira config from .workflow/config.json."""
    config_path = root / ".workflow" / "config.json"
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}", file=sys.stderr)
        print("Create .workflow/config.json with jira.base_url, jira.auth_env_var, jira.email_env_var", file=sys.stderr)
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    jira = config.get("jira")
    if not jira:
        print("Error: No 'jira' section in .workflow/config.json", file=sys.stderr)
        sys.exit(1)

    if not jira.get("base_url"):
        print("Error: jira.base_url is required in .workflow/config.json", file=sys.stderr)
        sys.exit(1)

    return jira


def resolve_ticket_key(ticket_input: str, config: dict) -> str:
    """Resolve input to a full ticket key (e.g., PROJ-456)."""
    if re.match(r"^[A-Z][A-Z0-9]+-\d+$", ticket_input):
        return ticket_input

    if re.match(r"^\d+$", ticket_input):
        default_project = config.get("default_project")
        if not default_project:
            print(f"Error: Numeric ticket ID '{ticket_input}' requires jira.default_project in config", file=sys.stderr)
            sys.exit(1)
        return f"{default_project}-{ticket_input}"

    print(f"Error: Invalid ticket format: '{ticket_input}'. Expected PROJ-456 or 456.", file=sys.stderr)
    sys.exit(1)


def fetch_ticket(base_url: str, ticket_key: str, auth_header: str) -> dict:
    """Fetch ticket from Jira REST API v3."""
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{ticket_key}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth_header}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Error: Ticket {ticket_key} not found", file=sys.stderr)
        elif e.code == 401:
            print("Error: Authentication failed. Check JIRA_EMAIL and JIRA_TOKEN.", file=sys.stderr)
        elif e.code == 403:
            print(f"Error: Permission denied for {ticket_key}", file=sys.stderr)
        else:
            print(f"Error: Jira API returned {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Could not connect to Jira: {e.reason}", file=sys.stderr)
        sys.exit(1)


def fetch_comments(base_url: str, ticket_key: str, auth_header: str, max_comments: int) -> list:
    """Fetch comments for a ticket."""
    url = f"{base_url.rstrip('/')}/rest/api/3/issue/{ticket_key}/comment?orderBy=-created&maxResults={max_comments}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Basic {auth_header}")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("comments", [])
    except (urllib.error.HTTPError, urllib.error.URLError):
        return []


# ---------------------------------------------------------------------------
# ADF (Atlassian Document Format) → Markdown transformer
# ---------------------------------------------------------------------------

def adf_to_markdown(node: dict | list | None) -> str:
    """Transform an ADF document node to markdown."""
    if node is None:
        return ""
    if isinstance(node, list):
        return "".join(adf_to_markdown(n) for n in node)
    if not isinstance(node, dict):
        return str(node)

    node_type = node.get("type", "")
    content = node.get("content", [])
    attrs = node.get("attrs", {})

    handler = ADF_HANDLERS.get(node_type)
    if handler:
        return handler(node, content, attrs)

    # Fallback: process children
    return adf_to_markdown(content)


def _adf_doc(node, content, attrs):
    return adf_to_markdown(content)


def _adf_paragraph(node, content, attrs):
    text = adf_to_markdown(content).strip()
    if not text:
        return "\n"
    return text + "\n\n"


def _adf_heading(node, content, attrs):
    level = attrs.get("level", 1)
    text = adf_to_markdown(content).strip()
    return f"{'#' * level} {text}\n\n"


def _adf_text(node, content, attrs):
    text = node.get("text", "")
    marks = node.get("marks", [])
    for mark in marks:
        mark_type = mark.get("type", "")
        if mark_type == "strong":
            text = f"**{text}**"
        elif mark_type == "em":
            text = f"*{text}*"
        elif mark_type == "code":
            text = f"`{text}`"
        elif mark_type == "strike":
            text = f"~~{text}~~"
        elif mark_type == "link":
            href = mark.get("attrs", {}).get("href", "")
            text = f"[{text}]({href})"
    return text


def _adf_hard_break(node, content, attrs):
    return "  \n"


def _adf_bullet_list(node, content, attrs):
    lines = []
    for item in content:
        item_text = _adf_list_item_text(item)
        lines.append(f"- {item_text}")
    return "\n".join(lines) + "\n\n"


def _adf_ordered_list(node, content, attrs):
    lines = []
    for i, item in enumerate(content, 1):
        item_text = _adf_list_item_text(item)
        lines.append(f"{i}. {item_text}")
    return "\n".join(lines) + "\n\n"


def _adf_list_item_text(item: dict) -> str:
    """Extract text from a listItem node, handling nested content."""
    parts = []
    for child in item.get("content", []):
        child_type = child.get("type", "")
        if child_type == "paragraph":
            parts.append(adf_to_markdown(child.get("content", [])).strip())
        elif child_type in ("bulletList", "orderedList"):
            nested = adf_to_markdown([child]).strip()
            indented = "\n".join("  " + line for line in nested.split("\n"))
            parts.append("\n" + indented)
        else:
            parts.append(adf_to_markdown([child]).strip())
    return " ".join(parts) if all(isinstance(p, str) and "\n" not in p for p in parts) else "\n".join(parts)


def _adf_code_block(node, content, attrs):
    lang = attrs.get("language", "")
    text = adf_to_markdown(content)
    return f"```{lang}\n{text}\n```\n\n"


def _adf_blockquote(node, content, attrs):
    text = adf_to_markdown(content).strip()
    quoted = "\n".join(f"> {line}" for line in text.split("\n"))
    return quoted + "\n\n"


def _adf_rule(node, content, attrs):
    return "---\n\n"


def _adf_table(node, content, attrs):
    rows = []
    for row_node in content:
        cells = []
        for cell in row_node.get("content", []):
            cell_text = adf_to_markdown(cell.get("content", [])).strip().replace("\n", " ")
            cells.append(cell_text)
        rows.append(cells)

    if not rows:
        return ""

    # First row as header
    header = rows[0]
    col_count = len(header)
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join(["---"] * col_count) + " |")
    for row in rows[1:]:
        # Pad row to match header column count
        padded = row + [""] * (col_count - len(row))
        lines.append("| " + " | ".join(padded[:col_count]) + " |")
    return "\n".join(lines) + "\n\n"


def _adf_media_single(node, content, attrs):
    for child in content:
        if child.get("type") == "media":
            media_attrs = child.get("attrs", {})
            alt = media_attrs.get("alt", "image")
            return f"[{alt}]\n\n"
    return ""


def _adf_mention(node, content, attrs):
    return f"@{attrs.get('text', attrs.get('id', 'unknown'))}"


def _adf_emoji(node, content, attrs):
    return attrs.get("text", attrs.get("shortName", ""))


def _adf_inline_card(node, content, attrs):
    url = attrs.get("url", "")
    return f"[link]({url})" if url else ""


def _adf_panel(node, content, attrs):
    panel_type = attrs.get("panelType", "info")
    text = adf_to_markdown(content).strip()
    return f"> **{panel_type.upper()}:** {text}\n\n"


def _adf_expand(node, content, attrs):
    title = attrs.get("title", "Details")
    text = adf_to_markdown(content).strip()
    return f"**{title}**\n\n{text}\n\n"


ADF_HANDLERS = {
    "doc": _adf_doc,
    "paragraph": _adf_paragraph,
    "heading": _adf_heading,
    "text": _adf_text,
    "hardBreak": _adf_hard_break,
    "bulletList": _adf_bullet_list,
    "orderedList": _adf_ordered_list,
    "codeBlock": _adf_code_block,
    "blockquote": _adf_blockquote,
    "rule": _adf_rule,
    "table": _adf_table,
    "mediaSingle": _adf_media_single,
    "mediaGroup": _adf_media_single,
    "mention": _adf_mention,
    "emoji": _adf_emoji,
    "inlineCard": _adf_inline_card,
    "panel": _adf_panel,
    "expand": _adf_expand,
}


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_output(ticket_key: str, issue: dict, comments: list) -> str:
    """Format Jira issue + comments as clean markdown."""
    fields = issue.get("fields", {})
    title = fields.get("summary", "Untitled")
    status = fields.get("status", {}).get("name", "Unknown")
    issue_type = fields.get("issuetype", {}).get("name", "Unknown")
    priority = fields.get("priority", {}).get("name", "")

    lines = [f"# {ticket_key}: {title}", ""]

    meta_parts = [f"**Status:** {status}", f"**Type:** {issue_type}"]
    if priority:
        meta_parts.append(f"**Priority:** {priority}")
    lines.append(" | ".join(meta_parts))
    lines.append("")

    # Description (ADF body)
    description_adf = fields.get("description")
    if description_adf:
        lines.append("## Description")
        lines.append("")
        lines.append(adf_to_markdown(description_adf).strip())
        lines.append("")

    # Acceptance criteria — check common custom field names and description patterns
    ac = _extract_acceptance_criteria(fields)
    if ac:
        lines.append("## Acceptance Criteria")
        lines.append("")
        lines.append(ac.strip())
        lines.append("")

    # Comments
    if comments:
        lines.append("## Comments")
        lines.append("")
        for comment in comments:
            author = comment.get("author", {}).get("displayName", "Unknown")
            created = comment.get("created", "")[:10]  # YYYY-MM-DD
            body = adf_to_markdown(comment.get("body"))
            lines.append(f"**{author}** ({created}):")
            lines.append("")
            lines.append(body.strip())
            lines.append("")
            lines.append("---")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _extract_acceptance_criteria(fields: dict) -> str | None:
    """Try to find acceptance criteria from custom fields or description."""
    # Check common custom field patterns
    for key, value in fields.items():
        if not key.startswith("customfield_"):
            continue
        if isinstance(value, dict) and value.get("type") == "doc":
            # Could be an ADF field — we can't know the name without field metadata.
            # Skip unnamed custom fields to avoid false positives.
            continue
        if isinstance(value, str) and len(value) > 20:
            # Heuristic: some orgs use a text custom field for AC.
            # Can't reliably identify without field names.
            continue

    # Try extracting from description text
    desc = fields.get("description")
    if desc:
        desc_md = adf_to_markdown(desc)
        # Look for "Acceptance Criteria" heading in the description
        ac_match = re.search(
            r"#+\s*Acceptance\s+Criteria\s*\n(.*?)(?=\n#+\s|\Z)",
            desc_md,
            re.IGNORECASE | re.DOTALL,
        )
        if ac_match:
            return ac_match.group(1).strip()

    return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Fetch a Jira ticket and output clean markdown.",
        usage="python .claude/scripts/jira_fetch.py PROJ-456 [--comments N]",
    )
    parser.add_argument("ticket", help="Ticket ID: PROJ-456 or just 456 (uses default_project)")
    parser.add_argument("--comments", type=int, default=5, help="Max comments to include (default: 5)")
    args = parser.parse_args()

    root = find_project_root()
    config = load_config(root)

    ticket_key = resolve_ticket_key(args.ticket, config)

    # Build auth header
    email_var = config.get("email_env_var", "JIRA_EMAIL")
    token_var = config.get("auth_env_var", "JIRA_TOKEN")

    email = os.environ.get(email_var)
    token = os.environ.get(token_var)

    if not email:
        print(f"Error: Environment variable {email_var} not set", file=sys.stderr)
        sys.exit(1)
    if not token:
        print(f"Error: Environment variable {token_var} not set", file=sys.stderr)
        sys.exit(1)

    auth_header = base64.b64encode(f"{email}:{token}".encode()).decode()
    base_url = config["base_url"]

    # Fetch
    issue = fetch_ticket(base_url, ticket_key, auth_header)
    comments = fetch_comments(base_url, ticket_key, auth_header, args.comments)

    # Output
    print(format_output(ticket_key, issue, comments))


if __name__ == "__main__":
    main()
