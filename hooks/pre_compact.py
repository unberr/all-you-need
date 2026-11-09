#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from stop_gate import CHECK_CMD, EDIT_TOOLS, OPEN_ITEM, entry_parts              

CHECKPOINT = Path(".all-you-need") / "checkpoint.md"
LEDGER = Path(".all-you-need") / "tasks.md"
MAX_GOAL = 500
MAX_NOTE = 700
MAX_FILES = 40
MAX_CHECKS = 20
MAX_LEDGER = 2500

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
    re.compile(r"\b(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{36,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bsk-proj-[A-Za-z0-9._-]{20,}\b"),
    re.compile(r"\bpplx-[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b|\bAK[A-Z0-9]{19}\b"),
    re.compile(r"(?i)\bauthorization\s*:\s*(?:bearer|basic|token)?\s*[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)[\"'](password|passwd|api[_-]?key|secret|token)[\"']\s*:\s*\"[^\"]+\""),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}"),
]


def clean(value: str, limit: int) -> str:
    for pattern in SECRET_PATTERNS:
        value = pattern.sub(lambda m: (m.group(1) + ": [redacted]") if m.lastindex else "[redacted]", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value[:limit] + ("..." if len(value) > limit else "")


def transcript_state(transcript: Path) -> dict:
    state = {"goal": "", "edits": {}, "checks": [], "note": ""}
    try:
        lines = transcript.read_text(encoding="utf-8").splitlines()
    except OSError:
        return state
    running: dict[str, str] = {}
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind, prompt, content = entry_parts(entry)
        if prompt is not None:
            state["goal"] = prompt
            state["edits"] = {}
            state["checks"] = []
            state["note"] = ""
            running.clear()
        elif kind == "user":
            for block in content:
                if block.get("type") != "tool_result":
                    continue
                command = running.pop(block.get("tool_use_id", ""), "")
                if command:
                    state["checks"].append((command, "FAIL" if block.get("is_error") else "PASS"))
        elif kind == "assistant":
            texts = [b.get("text", "") for b in content if b.get("type") == "text"]
            if texts:
                state["note"] = "\n".join(texts)
            for block in content:
                if block.get("type") != "tool_use":
                    continue
                raw_input = block.get("input")
                tool_input = raw_input if isinstance(raw_input, dict) else {}
                path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
                if block.get("name") in EDIT_TOOLS and path:
                    state["edits"][path] = state["edits"].get(path, 0) + 1
                command = tool_input.get("command", "") if block.get("name") == "Bash" else ""
                if command and CHECK_CMD.search(command):
                    running[block.get("id", "")] = command
    return state


def ledger_items(cwd: Path) -> list[str]:
    try:
        return OPEN_ITEM.findall((cwd / LEDGER).read_text(encoding="utf-8"))
    except OSError:
        return []


def build_checkpoint(transcript: Path, cwd: Path, trigger: str = "pre-compact") -> str:
    state = transcript_state(transcript)
    goal = clean(state["goal"], MAX_GOAL) or "(no user message found in the transcript)"
    note = clean(state["note"], MAX_NOTE) or "(none)"
    lines = [
        "# Session checkpoint",
        "",
        f"Written: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Trigger: {trigger}",
        f"Working directory: {cwd}",
        "",
        "## Goal (last user message, truncated)",
        goal,
        "",
        "## Files edited this turn",
    ]
    edits = list(state["edits"].items())[-MAX_FILES:]
    lines.extend(f"- `{path}` ({count} edit{'s' if count != 1 else ''})" for path, count in edits) if edits else \
        lines.append("- (none observed)")
    lines += ["", "## Checks run this turn"]
    checks = state["checks"][-MAX_CHECKS:]
    lines.extend(f"- {result}: `{clean(command, 200)}`" for command, result in checks) if checks else \
        lines.append("- (none observed)")
    open_items = ledger_items(cwd)
    if open_items:
        lines += ["", "## Open ledger items"]
        lines.extend(f"- [ ] {clean(item, 200)}" for item in open_items[:20])
        if len(open_items) > 20:
            lines.append(f"- ...and {len(open_items) - 20} more in .all-you-need/tasks.md")
    lines += ["", "## Last assistant note (truncated)", note, ""]
    text = "\n".join(lines)
    return text[:max(MAX_LEDGER + 1500, 2000)]


def write_checkpoint(transcript: Path, cwd: Path, trigger: str = "pre-compact") -> Path:
    target = cwd / CHECKPOINT
    if target.is_symlink():
        return target
    try:
        if not transcript or str(transcript) in ("", ".") or transcript.is_symlink():
            return target
        if transcript.exists() and transcript.stat().st_size > 5_000_000:
            return target
    except OSError:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_checkpoint(transcript, cwd, trigger), encoding="utf-8")
    return target


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
    if os.environ.get("ALL_YOU_NEED_OFF") == "1":
        return
    try:
        event = read_event()
    except (json.JSONDecodeError, ValueError):
        return
    cwd = Path(event.get("cwd") or os.getcwd())
    transcript = Path(event.get("transcript_path") or "")
    trigger = str(event.get("trigger") or "pre-compact")
    try:
        write_checkpoint(transcript, cwd, trigger)
    except OSError:
        return                                                                      


if __name__ == "__main__":
    main()
