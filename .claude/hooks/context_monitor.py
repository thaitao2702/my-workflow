#!/usr/bin/env python3
"""Context usage monitor — warns when context window is filling up.

PostToolUse hook that estimates context usage from transcript file size.
Injects warnings at threshold levels to prevent quality degradation.

Estimation approach: transcript file size ÷ ~4 bytes per token (rough estimate).
Not perfectly accurate, but sufficient for early warning.
"""

import json
import os
import sys

# Thresholds as percentage of context REMAINING
WARN_THRESHOLD = 35  # ≤35% remaining → WARNING
CRITICAL_THRESHOLD = 25  # ≤25% remaining → CRITICAL
STOP_THRESHOLD = 15  # ≤15% remaining → STOP

# Approximate context window sizes by model (tokens)
MODEL_CONTEXT = {
    "default": 200_000,
    "opus": 200_000,
    "sonnet": 200_000,
    "haiku": 200_000,
}

# Rough bytes-per-token estimate (conversation JSON includes overhead)
BYTES_PER_TOKEN = 6


def estimate_usage(transcript_path: str) -> float | None:
    """Estimate context usage percentage from transcript file size."""
    if not transcript_path or not os.path.exists(transcript_path):
        return None

    try:
        file_size = os.path.getsize(transcript_path)
        estimated_tokens = file_size / BYTES_PER_TOKEN
        context_limit = MODEL_CONTEXT["default"]
        usage_pct = (estimated_tokens / context_limit) * 100
        return min(usage_pct, 100)
    except OSError:
        return None


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)

    transcript_path = data.get("transcript_path", "")
    usage_pct = estimate_usage(transcript_path)

    if usage_pct is None:
        sys.exit(0)

    remaining_pct = 100 - usage_pct

    message = None
    if remaining_pct <= STOP_THRESHOLD:
        message = (
            f"🛑 CONTEXT CRITICAL ({remaining_pct:.0f}% remaining). "
            f"Save current state to state.json immediately. "
            f"Complete the current task, then STOP execution. "
            f"Do NOT start new tasks. Write a session handoff note."
        )
    elif remaining_pct <= CRITICAL_THRESHOLD:
        message = (
            f"⚠️ CONTEXT LOW ({remaining_pct:.0f}% remaining). "
            f"Complete the current task, then consider pausing. "
            f"Update state.json with current progress. "
            f"Avoid loading large files or spawning new agents."
        )
    elif remaining_pct <= WARN_THRESHOLD:
        message = (
            f"📊 Context usage notice: {remaining_pct:.0f}% remaining. "
            f"Be mindful of context — keep file reads targeted, "
            f"avoid loading entire large files."
        )

    if message:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": message,
            }
        }
        json.dump(output, sys.stdout)

    sys.exit(0)


if __name__ == "__main__":
    main()
