#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import platform
import re
import sys
from pathlib import Path

RULES = Path(__file__).with_name("core-rules.md")
LEDGER = Path(".all-you-need") / "tasks.md"
CHECKPOINT = Path(".all-you-need") / "checkpoint.md"
LESSONS_INDEX = Path(".claude") / "lessons" / "INDEX.md"
MAX_LEDGER_CHARS = 6000
MAX_LESSON_CHARS = 3000
MAX_CHECKPOINT_CHARS = 4000

JS_LOCKS = {"bun.lockb": "bun", "bun.lock": "bun", "pnpm-lock.yaml": "pnpm", "package-lock.json": "npm", "yarn.lock": "yarn"}
PY_LOCKS = {"uv.lock": "uv", "poetry.lock": "poetry", "Pipfile.lock": "pipenv"}
OTHER_LOCKS = {"Cargo.lock": "cargo", "go.sum": "go modules", "Gemfile.lock": "bundler", "composer.lock": "composer"}
RUNTIME_FILES = [".nvmrc", ".node-version", ".tool-versions", ".python-version", "rust-toolchain.toml", "rust-toolchain", "global.json"]
WORKSPACE_FILES = ["pnpm-workspace.yaml", "turbo.json", "nx.json", "lerna.json", "go.work"]
INSTRUCTION_FILES = ["CLAUDE.md", "AGENTS.md", ".cursorrules", ".github/copilot-instructions.md", "CONTRIBUTING.md", ".agents"]
SCRIPT_NAMES = ("dev", "start", "build", "test", "lint", "typecheck", "check", "format")


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
    except (json.JSONDecodeError, ValueError):                     
        return {}
    return _clean(data) if isinstance(data, dict) else {}


def _json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def detect_project(cwd: Path) -> str:
    lines: list[str] = []
    try:
        names = {p.name for p in cwd.iterdir()} if cwd.is_dir() else set()
    except OSError:
        return ""

    js = sorted(JS_LOCKS[n] for n in names if n in JS_LOCKS)
    js_unique = sorted(set(js))
    package = _json(cwd / "package.json") if "package.json" in names else {}
    declared = str(package.get("packageManager", "")).split("@")[0]
    if js_unique:
        lines.append(f"- JavaScript package manager: {', '.join(js_unique)} (from {', '.join(sorted(n for n in names if n in JS_LOCKS))})")
        if len(js_unique) > 1:
            lines.append("- CONFLICT: more than one JavaScript lockfile. Do not pick one yourself: check which is current and what CI uses, and ask the user if unclear.")
        if declared and declared not in js_unique:
            lines.append(f"- CONFLICT: package.json packageManager says {declared} but the lockfile says {', '.join(js_unique)}. Ask the user which is right.")
    elif package:
        lines.append("- package.json present with no lockfile: ask before installing anything.")
    py = sorted(PY_LOCKS[n] for n in names if n in PY_LOCKS)
    if py:
        lines.append(f"- Python environment manager: {', '.join(py)}")
        if len(py) > 1:
            lines.append("- CONFLICT: more than one Python lockfile. Ask the user which is current.")
    elif "requirements.txt" in names or "pyproject.toml" in names:
        lines.append("- Python: pip with requirements.txt or pyproject.toml (no lockfile found)")
    others = [OTHER_LOCKS[n] for n in names if n in OTHER_LOCKS]
    if others:
        lines.append(f"- Other ecosystems: {', '.join(sorted(others))}")
    if "mvnw" in names or "gradlew" in names:
        lines.append("- Use the committed wrapper (mvnw or gradlew), not a system install.")
    if any(n.endswith((".sln", ".csproj")) for n in names):
        lines.append("- .NET solution or project found: use dotnet with the SDK from global.json if present.")

    runtimes = [n for n in RUNTIME_FILES if n in names]
    engines = package.get("engines")
    if runtimes or engines:
        lines.append(f"- Runtime pins: {', '.join(runtimes + (['package.json engines'] if engines else []))} (read them; do not assume the installed version)")

    raw_scripts = package.get("scripts")
    scripts = raw_scripts if isinstance(raw_scripts, dict) else {}
    found = [f"{s}" for s in SCRIPT_NAMES if s in scripts]
    if found:
        lines.append(f"- package.json scripts: {', '.join(found)}. Use these, not guessed commands.")
    if "Makefile" in names:
        try:
            targets = re.findall(r"^(test|build|lint|check|fmt|format|typecheck|ci)\s*:", (cwd / "Makefile").read_text(encoding="utf-8"), re.M)
        except OSError:
            targets = []
        if targets:
            lines.append(f"- Makefile targets: {', '.join(dict.fromkeys(targets))}")

    layout = [n for n in WORKSPACE_FILES if n in names]
    if package.get("workspaces"):
        layout.append("package.json workspaces")
    if "Cargo.toml" in names:
        try:
            if re.search(r"^\[workspace\]", (cwd / "Cargo.toml").read_text(encoding="utf-8"), re.M):
                layout.append("Cargo workspace")
        except OSError:
            pass
    if layout:
        lines.append(f"- Monorepo markers: {', '.join(layout)}. Find the package you are in and run commands from there unless the tooling says otherwise.")

    instructions = [n for n in INSTRUCTION_FILES if (cwd / n).exists()]
    if instructions:
        lines.append(f"- Project instruction files: {', '.join(instructions)}. Read them and every file they include; the one nearest the file you edit wins.")

    if not lines:
        return ""
    header = f"\n\nProject facts detected from files in {cwd.name or str(cwd)} (OS: {platform.system()}). Re-check before relying on them:\n"
    return header + "\n".join(lines) + "\n"


def lessons_text(cwd: Path) -> str:
    index = cwd / LESSONS_INDEX
    if index.is_symlink():
        return ""
    try:
        text = index.read_text(encoding="utf-8")
    except OSError:
        return ""
    clipped = text[:MAX_LESSON_CHARS] + ("\n...(index truncated: read the file)" if len(text) > MAX_LESSON_CHARS else "")
    return ("\n\nLesson index (.claude/lessons/INDEX.md). Open the ones relevant to this task. A lesson that names a file, "
            "function or flag describes what was true when written: confirm it still exists:\n\n" + clipped + "\n")


def checkpoint_text(cwd: Path) -> str:
    path = cwd / CHECKPOINT
    if path.is_symlink():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    if not text.strip():
        return ""
    clipped = text[:MAX_CHECKPOINT_CHARS] + ("\n...(checkpoint truncated: read .all-you-need/checkpoint.md)"
                                             if len(text) > MAX_CHECKPOINT_CHARS else "")
    return ("\n\nCheckpoint written before the last context compaction. Treat it as historical: confirm paths and "
            "results against the working tree before acting, and continue at the first unfinished item:\n\n" + clipped + "\n")


def ledger_text(cwd: Path) -> str:
    path = cwd / LEDGER
    if path.is_symlink():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    if "- [ ]" not in text:
        return ""
    clipped = text[:MAX_LEDGER_CHARS] + ("\n...(ledger truncated: read the file)" if len(text) > MAX_LEDGER_CHARS else "")
    return ("\n\nUnfinished task ledger (.all-you-need/tasks.md). Resume at the first open item; do not restart "
            "finished items and do not re-ask what the ledger already answers:\n\n" + clipped + "\n")


def main() -> None:
    if os.environ.get("ALL_YOU_NEED_OFF") == "1":
        return
    cwd = Path(read_event().get("cwd") or os.getcwd())
    try:
        sys.stdout.write(RULES.read_text(encoding="utf-8") + detect_project(cwd) + checkpoint_text(cwd)
                         + lessons_text(cwd) + ledger_text(cwd))
    except OSError:
        try:
            sys.stdout.write(detect_project(cwd) + checkpoint_text(cwd) + lessons_text(cwd) + ledger_text(cwd))
        except OSError:
            return


if __name__ == "__main__":
    main()
