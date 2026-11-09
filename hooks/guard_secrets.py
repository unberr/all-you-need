#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import PurePath

ALLOW_ENV = "ALL_YOU_NEED_ALLOW_SECRET_READS"
TEMPLATE_SUFFIX = re.compile(r"\.(example|sample|template|dist)$", re.I)
SECRET_NAME = re.compile(
    r"^(\.env(\..+)?|.+\.env|\.envrc|\.env\.local|.+\.envrc|.+\.env\.local|.+\.pem|.+\.key|.+\.p12|.+\.pfx|.+\.jks|.+\.keystore|id_(rsa|dsa|ecdsa|ed25519)(\.pub)?"
    r"|\.netrc|\.pypirc|\.npmrc|\.git-credentials|credentials(\.json)?|.*service[-_]?account.*\.json|secrets?\.(ya?ml|json|toml)|"
    r"terraform\.tfstate.*|\.docker[\\/]config\.json)$",
    re.I)
READ_VERBS = r"(cat|less|more|head|tail|grep|rg|ag|sed|awk|base64|xxd|od|strings|scp|rsync|curl|wget|source|bat|nl|python3?|node|openssl|cp|mv|tar|zip|unzip|dd|printenv|env)"
SECRET_IN_COMMAND = re.compile(
    r"(^|[\s;&|(<=@\"'/])(\.env(\.[\w.-]+)?|[\w.-]+\.(pem|key|p12|pfx|jks|keystore)|id_(rsa|dsa|ecdsa|ed25519)|\.netrc|\.pypirc|\.git-credentials)(?=$|[\s;&|)\"'])",
    re.I)


def is_secret_path(path: str) -> bool:
    name = PurePath(path.replace("\\", "/")).name
    return bool(name) and bool(SECRET_NAME.match(name)) and not TEMPLATE_SUFFIX.search(name)


def command_touches_secret(command: str) -> bool:
    if not re.search(rf"\b{READ_VERBS}\b|<", command):
        return False
                                                                          
                                                                   
    stripped = command.strip()
    if re.match(r"(sudo\s+)?(cp|mv)\s+\S*\.example\b", stripped):
        rest = re.sub(r"^(sudo\s+)?(cp|mv)\s+\S+\s*", "", stripped)
                                                                          
        first = re.sub(r"^\S+\s*", "", rest)
        if first == "" or re.fullmatch(r"\.env(\.[\w.-]+)?", rest.split()[0] if rest.split() else ""):
            return False
    for match in SECRET_IN_COMMAND.finditer(command):
        if not TEMPLATE_SUFFIX.search(match.group(2)):
            return True
    return False


def denial(tool_name: str, tool_input: dict) -> str | None:
    if tool_name == "Read" and is_secret_path(tool_input.get("file_path", "")):
        return f"{tool_input.get('file_path')} holds credentials. Ask the user for the specific non-secret value you need, or read the .example template."
    if tool_name == "Bash" and command_touches_secret(tool_input.get("command", "")):
        return "This command reads or sends a credential file. Secrets stay out of the model's context; use the template file or ask the user."
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
    if os.environ.get(ALLOW_ENV) == "1":
        return
    event = read_event()
    reason = denial(event.get("tool_name", ""), event.get("tool_input") or {})
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": "all-you-need secret guard: " + reason}}))


if __name__ == "__main__":
    main()
