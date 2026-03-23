#!/usr/bin/env python3
"""Quality check hook — provides feedback after file writes.

PostToolUse hook for Write/Edit tools.
Checks for common quality issues and injects feedback into context.
Cannot undo changes (fires after execution) — only provides guidance.
"""

import json
import os
import sys


def check_quality(tool_name: str, tool_input: dict) -> list[str]:
    """Check for quality issues in written/edited files."""
    warnings = []

    file_path = tool_input.get("file_path", "")
    content = tool_input.get("content", "") or tool_input.get("new_string", "")

    if not file_path or not content:
        return warnings

    filename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    # Check: console.log / print statements in production code
    test_indicators = ["test", "spec", "__tests__", ".test.", ".spec."]
    is_test = any(ind in file_path.lower() for ind in test_indicators)

    if not is_test:
        debug_patterns = {
            ".ts": ["console.log(", "console.debug("],
            ".tsx": ["console.log(", "console.debug("],
            ".js": ["console.log(", "console.debug("],
            ".jsx": ["console.log(", "console.debug("],
            ".py": ["print(", "breakpoint()"],
            ".go": ["fmt.Println(", "fmt.Printf("],
            ".rs": ["println!(", "dbg!("],
        }

        if ext in debug_patterns:
            for pattern in debug_patterns[ext]:
                if pattern in content:
                    warnings.append(
                        f"Debug output `{pattern}` found in production code. "
                        f"Use proper logging instead."
                    )
                    break

    # Check: TODO/FIXME/HACK without context
    for marker in ["TODO", "FIXME", "HACK", "XXX"]:
        if marker in content:
            # Check if it has a description after it
            lines = content.split("\n")
            for line in lines:
                if marker in line:
                    after = line.split(marker, 1)[1].strip().strip(":").strip()
                    if len(after) < 5:
                        warnings.append(
                            f"`{marker}` comment without description. "
                            f"Add context so it's actionable."
                        )
                        break

    # Check: empty catch/except blocks
    if ext in (".ts", ".tsx", ".js", ".jsx"):
        if "catch" in content and "catch (e) {}" in content.replace(" ", ""):
            warnings.append("Empty catch block detected. Errors should not be swallowed silently.")

    if ext == ".py":
        if "except:" in content or "except Exception:\n        pass" in content:
            warnings.append("Bare except or except-pass detected. Handle errors explicitly.")

    return warnings


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    warnings = check_quality(tool_name, tool_input)

    if warnings:
        context = "⚠️ Quality check findings:\n" + "\n".join(f"- {w}" for w in warnings)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": context,
            }
        }
        json.dump(output, sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
