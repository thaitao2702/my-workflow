#!/usr/bin/env python3
"""Security gate hook — blocks catastrophic commands, asks confirmation for risky ones.

PreToolUse hook for Bash and Write/Edit tools.
- Exit 0 + JSON with permissionDecision to allow/deny/ask
- Exit 2 + stderr message to block
"""

import json
import re
import sys


def check_bash_command(command: str) -> dict | None:
    """Check a bash command against security rules."""
    cmd_lower = command.lower().strip()

    # === BLOCKED (always) ===
    blocked_patterns = [
        (r"drop\s+database", "DROP DATABASE is blocked — catastrophic data loss"),
        (r"truncate\s+table", "TRUNCATE TABLE is blocked — catastrophic data loss"),
        (r"rm\s+-rf\s+/(?:\s|$)", "rm -rf / is blocked — system destruction"),
        (r"git\s+push\s+.*--force.*\s+(main|master)", "Force push to main/master is blocked"),
        (r"git\s+push\s+.*\s+(main|master).*--force", "Force push to main/master is blocked"),
        (r"curl\s+.*\|\s*(?:sudo\s+)?(?:ba)?sh", "Piped remote execution is blocked"),
        (r"wget\s+.*\|\s*(?:sudo\s+)?(?:ba)?sh", "Piped remote execution is blocked"),
    ]

    for pattern, reason in blocked_patterns:
        if re.search(pattern, cmd_lower):
            return {"decision": "deny", "reason": reason}

    # === ASK CONFIRMATION ===
    ask_patterns = [
        (r"git\s+reset\s+--hard", "git reset --hard — this discards uncommitted changes"),
        (r"drop\s+column|drop\s+table|alter\s+table.*drop", "Destructive database migration detected"),
        (r"npm\s+install\s+\S", "Installing new npm dependency"),
        (r"pip\s+install\s+\S", "Installing new pip dependency"),
        (r"cargo\s+add\s+\S", "Installing new cargo dependency"),
        (r"rm\s+-rf?\s+", "File deletion detected — verify target is correct"),
    ]

    for pattern, reason in ask_patterns:
        if re.search(pattern, cmd_lower):
            return {"decision": "ask", "reason": reason}

    return None


def check_file_content(content: str, file_path: str) -> dict | None:
    """Check written file content for hardcoded secrets."""
    secret_patterns = [
        (r"(?:api[_-]?key|apikey)\s*[:=]\s*['\"][A-Za-z0-9_\-]{20,}['\"]", "Possible hardcoded API key"),
        (r"(?:secret|password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]", "Possible hardcoded secret/password"),
        (r"(?:token)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{20,}['\"]", "Possible hardcoded token"),
        (r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----", "Private key detected in source code"),
    ]

    # Skip config/env example files
    skip_extensions = {".env.example", ".env.sample", ".env.template"}
    if any(file_path.endswith(ext) for ext in skip_extensions):
        return None

    for pattern, reason in secret_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            return {"decision": "ask", "reason": f"{reason} in {file_path}"}

    return None


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    result = None

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        result = check_bash_command(command)

    elif tool_name in ("Write", "Edit"):
        content = tool_input.get("content", "") or tool_input.get("new_string", "")
        file_path = tool_input.get("file_path", "")
        if content and file_path:
            result = check_file_content(content, file_path)

    if result:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": result["decision"],
                "permissionDecisionReason": result["reason"],
            }
        }
        json.dump(output, sys.stdout)
        sys.exit(0)

    # No issues found — allow
    sys.exit(0)


if __name__ == "__main__":
    main()
