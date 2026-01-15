#!/usr/bin/env python3
"""Custom status line for Claude Code - displays context, cost, model, git branch, and version."""

from __future__ import annotations

import json
import subprocess
import sys


def get_git_branch() -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass
    return ""


def get_git_changes() -> tuple[int, int]:
    """Get lines added and removed from git status."""
    try:
        result = subprocess.run(
            ["git", "diff", "--shortstat", "HEAD"],
            capture_output=True,
            text=True,
            timeout=1,
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            added = 0
            removed = 0
            if "insertion" in output:
                for part in output.split(","):
                    if "insertion" in part:
                        added = int(part.strip().split()[0])
                    elif "deletion" in part:
                        removed = int(part.strip().split()[0])
            return added, removed
    except (subprocess.SubprocessError, OSError, ValueError):
        pass
    return 0, 0


def get_context_percentage(data: dict) -> str:
    """Calculate context percentage using official Claude Code formula."""
    context_window = data.get("context_window", {})
    context_size = context_window.get("context_window_size", 200000)
    current_usage = context_window.get("current_usage")

    if not current_usage:
        return "Ctx: 0%"

    input_tokens = current_usage.get("input_tokens", 0)
    cache_creation = current_usage.get("cache_creation_input_tokens", 0)
    cache_read = current_usage.get("cache_read_input_tokens", 0)

    total_tokens = input_tokens + cache_creation + cache_read
    percentage = (total_tokens / context_size) * 100

    return f"Ctx: {percentage:.1f}%"


def get_cost(data: dict) -> str:
    """Get session cost."""
    cost_data = data.get("cost", {})
    total_cost = cost_data.get("total_cost_usd", 0)

    if total_cost > 0:
        return f"${total_cost:.2f}"
    return ""


def main() -> None:
    """Generate status line from Claude Code JSON input."""
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        print("Status line error")
        return

    model = data.get("model", {}).get("display_name", "Unknown")
    version = data.get("version", "")

    branch = get_git_branch()
    added, removed = get_git_changes()

    parts = [f"Model: {model}"]

    context_pct = get_context_percentage(data)
    parts.append(context_pct)

    cost = get_cost(data)
    if cost:
        parts.append(cost)

    if branch:
        parts.append(f"\u23c7 {branch}")

    if added or removed:
        parts.append(f"(+{added},-{removed})")

    if version:
        parts.append(f"v{version}")

    print(" | ".join(parts))


if __name__ == "__main__":
    main()
