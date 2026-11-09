#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import guard_actions              
import guard_config              
import guard_secrets              

OFF_ENV = "ALL_YOU_NEED_OFF"
EDIT_TOOLS = {"Edit", "Write", "MultiEdit"}


def decide(event: dict) -> tuple[str, str] | None:
    name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    found: list[tuple[str, str]] = []
    if os.environ.get(guard_secrets.ALLOW_ENV) != "1":
        reason = guard_secrets.denial(name, tool_input)
        if reason:
            found.append(("deny", "all-you-need secret guard: " + reason))
    if name == "Bash" and os.environ.get(guard_actions.ALLOW_ENV) != "1":
        action = guard_actions.decision(tool_input.get("command", ""))
        if action:
            found.append((action[0], f"all-you-need action guard: {action[1]}"))
    if name in EDIT_TOOLS and os.environ.get(guard_config.ALLOW_ENV) != "1":
        path = tool_input.get("file_path", "")
        reasons = guard_config.weakening(path, guard_config.added_text(name, tool_input))
        if reasons:
            filename = Path(path.replace("\\", "/")).name
            found.append(("ask", f"all-you-need config guard: this edit to {filename} {'; '.join(reasons)}. "
                                 "Fix the code the check complains about instead, unless the user asked to change the rule."))
    for verb in ("deny", "ask"):
        for decision, reason in found:
            if decision == verb:
                return decision, reason
    return None


def main() -> None:
    if os.environ.get(OFF_ENV) == "1":
        return
    decision = decide(guard_secrets.read_event())
    if decision:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": decision[0],
                                                 "permissionDecisionReason": decision[1]}}))


if __name__ == "__main__":
    main()
