#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cve_check              
import slop_lint              

OFF_ENV = "ALL_YOU_NEED_OFF"


def notes_for(event: dict) -> list[str]:
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    notes: list[str] = []
    found = slop_lint.findings(path, slop_lint.added_text(event.get("tool_name", ""), tool_input))
    if found:
        notes.append(f"all-you-need quality check on {path}:\n- " + "\n- ".join(found)
                     + "\nFix these in your next edit unless the user asked for them.")
    dependency_note = cve_check.check(path)
    if dependency_note:
        notes.append(dependency_note)
    return notes


def main() -> None:
    if os.environ.get(OFF_ENV) == "1":
        return
    notes = notes_for(slop_lint.read_event())
    if notes:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": "\n\n".join(notes)}}))


if __name__ == "__main__":
    main()
