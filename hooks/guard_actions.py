#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys

ALLOW_ENV = "ALL_YOU_NEED_ALLOW_ACTIONS"

DENY = [
    (re.compile(r"\bgit\b[^|;&]*\s(--no-verify|--no-gpg-sign)\b|\bgit\s+commit\b[^|;&]*\s-n\b|\bgit\s+commit\b[^|;&]*\s-nm\b"),
     "Skipping hooks or signing is not allowed. If a hook fails, fix the cause."),
    (re.compile(r"\bgit\b[^|;&]*(-c\s+core\.hooksPath|core\.hooksPath\s*=)"),
     "Overriding the hooks path is not allowed."),
    (re.compile(r"(?i)\bHUSKY\s*=\s*0\b"),
     "Disabling husky hooks is not allowed."),
]

ASK = [
    (re.compile(r"\bgit\s+(-C\s+\S+\s+|--no-pager\s+)?(reset\s+--hard|push\b|commit\b|checkout\b|restore\b)"), "Git state rewrite/publish via wrapper flags still needs approval."),
    (re.compile(r"\bgit\s+reset\s+--hard\b"), "git reset --hard discards uncommitted work and cannot be undone."),
    (re.compile(r"\bgit\s+push\b[^|;&]*(\s--force\b|\s--force-with-lease\b|\s-f\b|\s\+\w)"), "Force-pushing rewrites remote history."),
    (re.compile(r"\bgit\s+clean\b[^|;&]*\s-\w*[fdx]"), "git clean deletes untracked files permanently."),
    (re.compile(r"\bgit\s+branch\b[^|;&]*\s-D\b"), "git branch -D deletes a branch even if unmerged."),
    (re.compile(r"\bgit\s+(checkout|restore)\b[^|;&]*(\s--\s+\.|\s\.\s*$|\s--source)"), "This discards uncommitted changes in the working tree."),
    (re.compile(r"\bgit\s+(rebase|filter-branch|filter-repo)\b|\bgit\s+commit\b[^|;&]*--amend\b"), "This rewrites history."),
    (re.compile(r"\bgit\s+push\b[^|;&]*\b(origin\s+)?(main|master|trunk|develop)\b"), "This pushes directly to a default branch. Branch first unless you were told to."),
    (re.compile(r"\bgit\s+push\b"), "Pushing publishes commits to a remote."),
    (re.compile(r"\brm\s+(?=[^|;&]*-[a-zA-Z]*r)(?=[^|;&]*-[a-zA-Z]*f)"), "Recursive forced deletion cannot be undone."),
    (re.compile(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|--recursive)\b"), "Recursive deletion cannot be undone."),
    (re.compile(r"(?i)\b(drop|truncate)\s+(table|database|schema)\b|\bdelete\s+from\s+\w+\s*(;|$)"), "This destroys database data."),
    (re.compile(r"\b(terraform|tofu|pulumi)\s+(apply|destroy|up)\b|\bkubectl\s+(delete|apply|replace)\b|\bhelm\s+(install|upgrade|uninstall)\b|\baws\s+\S+\s+(delete|terminate|remove)"), "This changes live infrastructure."),
    (re.compile(r"\b(npm|pnpm|yarn)\s+publish\b|\btwine\s+upload\b|\bcargo\s+publish\b|\bgh\s+(release|repo)\s+(create|delete)\b|\bdocker\s+push\b"), "This publishes an artifact publicly."),
    (re.compile(r"\bgh\s+(pr|issue)\s+(create|comment|close|merge|edit)\b|\bgh\s+api\b[^|;&]*(-X|--method)\s+(POST|PUT|PATCH|DELETE)"), "This posts to a third-party service (outward-facing)."),
    (re.compile(r"\b(vercel|netlify|fly|railway|heroku)\b[^|;&]*\b(deploy|--prod|release)\b|\bsls\s+deploy\b|\bcdk\s+deploy\b"), "This deploys to a hosted environment."),
    (re.compile(r"\b(chmod|chown)\s+(-R|--recursive)\b"), "Recursive permission changes affect many files."),
    (re.compile(r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?((ba|z|da)?sh|python3?|node)\b"), "Piping a remote script into a shell runs unreviewed code."),
]


def _unquoted(command: str) -> str:
    out, quote, escaped, buf = [], "", False, ""
    for ch in command:
        if escaped:
            escaped = False
            continue
        if quote:
            if ch == "\\":
                escaped = True
            elif ch == quote:
                quote = ""
                out.append(" ")
            continue
        if ch in ("'", '"'):
            quote = ch
            buf = ""
            continue
        out.append(ch)
    return "".join(out)


def _inner_quoted(command: str) -> str:
    if not re.search(r"\b(bash|sh|eval|python3?|node)\b", command):
        return ""
    return " ".join(m.group(1) or m.group(2) for m in
                   re.finditer(r'"([^"]*)"|\'([^\']*)\'', command))


def decision(command: str) -> tuple[str, str] | None:
    text = _unquoted(command)
    inner = _inner_quoted(command)
    for target in ([text] if not inner else [text, inner]):
        for pattern, reason in DENY:
            if pattern.search(target):
                return "deny", reason
    for target in ([text] if not inner else [text, inner]):
        for pattern, reason in ASK:
            if pattern.search(target):
                return "ask", reason
    return None


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
    import os
    if os.environ.get(ALLOW_ENV) == "1":
        return
    event = read_event()
    if event.get("tool_name") != "Bash":
        return
    found = decision((event.get("tool_input") or {}).get("command", ""))
    if found:
        verb, reason = found
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": verb,
                                                 "permissionDecisionReason": f"all-you-need action guard: {reason}"}}))


if __name__ == "__main__":
    main()
