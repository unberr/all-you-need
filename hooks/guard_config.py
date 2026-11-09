#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import PurePath

ALLOW_ENV = "ALL_YOU_NEED_ALLOW_CONFIG_EDITS"
CONFIG_PATH = re.compile(
    r"(^|[\\/])(\.?eslintrc[^\\/]*|eslint\.config\.[^\\/]*|\.?prettierrc[^\\/]*|prettier\.config\.[^\\/]*|tsconfig[^\\/]*\.json|"
    r"biome\.jsonc?|ruff\.toml|\.ruff\.toml|pyproject\.toml|setup\.cfg|tox\.ini|mypy\.ini|\.mypy\.ini|pyrightconfig\.json|"
    r"\.pre-commit-config\.ya?ml|\.golangci\.ya?ml|rustfmt\.toml|clippy\.toml|\.rubocop\.yml|phpstan\.neon(\.dist)?|psalm\.xml|"
    r"phpcs\.xml(\.dist)?|\.stylelintrc[^\\/]*|jest\.config\.[^\\/]*|vitest\.config\.[^\\/]*|\.editorconfig|\.gitlab-ci\.ya?ml|"
    r"Directory\.Build\.props|\.globalconfig)$|\.github[\\/]workflows[\\/]|(^|[\\/])\.husky[\\/]",
    re.I)
WEAKENING = [
    (re.compile(r"(?i)[\"']?(strict|noImplicitAny|strictNullChecks|noUncheckedIndexedAccess|strictFunctionTypes|noImplicitReturns|"
                r"warnaserror|treatwarningsaserrors|nullable)[\"']?\s*[:=]\s*[\"']?(false|disable|0)\b"), "turns a strictness option off"),
    (re.compile(r"[\"'][\w@/.-]+[\"']\s*:\s*[\"']off[\"']|:\s*off\s*$", re.M), "disables a lint rule"),
    (re.compile(r"(?i)\b(extend-ignore|per-file-ignores|ignore_errors|ignore_missing_imports|disable_error_code)\b|\b(ignore|disable)\s*[:=]\s*\["), "adds ignores or disables checks"),
    (re.compile(r"(?i)continue-on-error:\s*true|allow_failure:\s*true|\|\|\s*true\b|--no-verify|skip[-_]?checks|if:\s*false"), "lets a pipeline or hook step fail silently"),
    (re.compile(r"(?i)\bskipLibCheck\b\s*[:=]\s*true|\b(coverage|cov)[-_]?(fail[-_]?under|threshold)\b\s*[:=]\s*\d+"), "relaxes a check or threshold"),
]


def added_text(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return tool_input.get("new_string", "")
    if tool_name == "MultiEdit":
        return "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    return ""


def weakening(path: str, text: str) -> list[str]:
    if not CONFIG_PATH.search(path.replace("\\", "/")) and not CONFIG_PATH.search(path):
        return []
    return [reason for pattern, reason in WEAKENING if pattern.search(text)]


def _clean(data: dict) -> dict:
    for key in ("cwd", "transcript_path", "tool_name"):
        if not isinstance(data.get(key), str):
            data[key] = ""
    tool_input = data.get("tool_input")
    tool_input = dict(tool_input) if isinstance(tool_input, dict) else {}
    for key in ("file_path", "notebook_path", "command", "new_string", "content"):
        if not isinstance(tool_input.get(key), str):
            tool_input[key] = ""
    edits = tool_input.get("edits")
    tool_input["edits"] = [dict(e, new_string=e["new_string"] if isinstance(e.get("new_string"), str) else "")
                           for e in edits if isinstance(e, dict)] if isinstance(edits, list) else []
    data["tool_input"] = tool_input
    return data


def read_event() -> dict:
    try:
        data = json.load(sys.stdin)
    except (ValueError, OSError):
        return {}
    return _clean(data) if isinstance(data, dict) else {}


def main() -> None:
    if os.environ.get(ALLOW_ENV) == "1":
        return
    event = read_event()
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    reasons = weakening(path, added_text(event.get("tool_name", ""), tool_input))
    if reasons:
        message = (f"all-you-need config guard: this edit to {PurePath(path.replace(chr(92), '/')).name} {'; '.join(reasons)}. "
                   "Fix the code the check complains about instead, unless the user asked to change the rule.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                                 "permissionDecisionReason": message}}))


if __name__ == "__main__":
    main()
