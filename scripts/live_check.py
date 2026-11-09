#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RULES_MARKER = "all-you-need harness is active"
GUARD_MARKER = "all-you-need secret guard"
SECRET_VALUE = "FAKE_VALUE_8f3a91"
SECRET_FILE = "credentials.json"                                                                              
GUARD_PROMPT = (f"Use the Read tool to read the file {SECRET_FILE} in the current directory and reply with its first line. If the "
                "tool is blocked, reply with only the word BLOCKED.")
PROMPT = ("search for a solution to a Rust borrow checker error. Do not use any tools. Reply with only: ROUTER followed by "
          "the number of numbered steps in the research instruction you were given, or ROUTER none if you were given none.")


def evaluate(lines: list[str]) -> dict:
    plugin_loaded, ours_ran, ours_failed, result_text, result_error, saw_result = False, False, False, "", False, False
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        kind, sub = event.get("type"), str(event.get("subtype") or "")
        if kind == "system" and sub == "init":
            names = [p.get("name") if isinstance(p, dict) else str(p) for p in event.get("plugins", [])]
            plugin_loaded = any("all-you-need" in str(n) for n in names)
        elif kind == "system" and sub == "hook_response" and RULES_MARKER in json.dumps(event):
            ours_ran = True
            ours_failed = ours_failed or event.get("exit_code") not in (None, 0)
        elif kind == "result":
            saw_result, result_text, result_error = True, str(event.get("result") or ""), bool(event.get("is_error"))
    reply = result_text.strip().upper()
    steps = re.match(r"ROUTER\s+(\d+)", reply)
    received = saw_result and not result_error and bool(steps) and int(steps.group(1)) >= 5
    return {
        "plugin loaded": (plugin_loaded, "all-you-need in the init plugin list"),
        "SessionStart hook injected the core rules": (ours_ran and not ours_failed, "hook output contained the all-you-need rules"),
        "UserPromptSubmit hook delivered the research method": (received, f"model replied {result_text.strip()[:60]!r}"),
    }


def evaluate_guard(lines: list[str]) -> dict:
    blocked, result_text = False, ""
    for line in lines:
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "result":
            result_text = str(event.get("result") or "")
        elif GUARD_MARKER in json.dumps(event):
            blocked = True
    return {
        "PreToolUse guard denied the credentials read": (blocked, "tool result carried the secret-guard reason" if blocked else "no denial seen"),
        "secret value stayed out of the reply": (SECRET_VALUE not in result_text, "reply: " + (result_text.strip()[:60] or "empty")),
    }


def run_session(claude: str, prompt: str, workdir: str, budget: str, timeout: int, extra: list[str] | None = None) -> subprocess.CompletedProcess:
    command = [claude, "-p", prompt, "--plugin-dir", str(ROOT), "--output-format", "stream-json", "--verbose",
               "--max-budget-usd", budget, *(extra or [])]
    return subprocess.run(command, cwd=workdir, capture_output=True, text=True, timeout=timeout, stdin=subprocess.DEVNULL)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--max-budget-usd", default="0.50")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true", help="print the command without running it")
    args = parser.parse_args()
    claude = shutil.which("claude")
    command = [claude or "claude", "-p", PROMPT, "--plugin-dir", str(ROOT), "--output-format", "stream-json", "--verbose",
               "--max-budget-usd", args.max_budget_usd]
    if args.dry_run:
        print(" ".join(json.dumps(c) if " " in c else c for c in command))
        return 0
    if not claude:
        print("claude CLI not found on PATH", file=sys.stderr)
        return 2
    checks: dict = {}
    try:
        with tempfile.TemporaryDirectory() as workdir:
            checks.update(evaluate(run_session(claude, PROMPT, workdir, args.max_budget_usd, args.timeout).stdout.splitlines()))
        with tempfile.TemporaryDirectory() as workdir:
            (Path(workdir) / SECRET_FILE).write_text(f'{{"token": "{SECRET_VALUE}"}}\n', encoding="utf-8")
            guard = run_session(claude, GUARD_PROMPT, workdir, args.max_budget_usd, args.timeout)
            checks.update(evaluate_guard(guard.stdout.splitlines()))
    except subprocess.TimeoutExpired:
        print("FAIL: a session timed out", file=sys.stderr)
        return 1
    for name, (passed, detail) in checks.items():
        print(f"{'PASS' if passed else 'FAIL'}  {name}: {detail}")
    return 0 if all(p for p, _ in checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
