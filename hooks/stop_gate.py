#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".rs", ".go", ".c", ".h", ".cc", ".cpp", ".hpp",
            ".swift", ".kt", ".java", ".rb", ".php", ".cs", ".sh", ".zsh", ".sql", ".vue", ".svelte", ".astro"}
EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
CHECK_CMD = re.compile(
    r"\b(pytest|jest|vitest|mocha|tsc|eslint|biome|ruff|mypy|pyright|clippy|shellcheck|semgrep|bandit|"
    r"cargo (build|check|test|clippy)|go (build|test|vet)|golangci-lint|staticcheck|govulncheck|"
    r"swift (build|test)|xcodebuild|gradlew?|mvnw?|dotnet (build|test|format)|"
    r"phpunit|phpstan|psalm|phpcs|pest|composer (test|run|audit|validate)|php -l|"
    r"clang-tidy|cppcheck|make|cmake|ctest|ninja|(npm|pnpm|yarn|bun|deno) (run|test|build|check|lint)|"
    r"python3? (-I )?-m (py_compile|unittest|pytest)|node (--check|--test)|bash -n|svelte-check|vue-tsc|"
    r"python3? (-I )?\S*(test_\w+|\w+_test)\.py)\b"
)
EXTRA_CHECK_ENV = "ALL_YOU_NEED_CHECK_CMD"                                                         
SECURITY_LINE = re.compile(r"^\W*security review( needed)?\s*:", re.I | re.M)
SECURITY_PATH = re.compile(
    r"(^|[\\/._-])(auth|authn|authz|login|logout|session|password|passwd|crypto|encrypt|decrypt|secret|secrets|token|jwt|"
    r"oauth|saml|sso|permission|permissions|rbac|acl|policy|payment|payments|billing|checkout|iam|cors|csp)([\\/._-]|$)"
    r"|dockerfile|docker-compose|\.github[\\/]workflows|\.gitlab-ci|\.tf$|terraform|helm|kubernetes|k8s|nginx|\.htaccess"
    r"|(^|[\\/])(hooks?|agents?|commands?)[\\/]|(^|[\\/])(plugin|marketplace)\.json$|settings\.json$|core-rules\.md$",
    re.I)
VERIFIED_LINE = re.compile(r"^\W*(not verified|unverified)\s*:", re.I | re.M)
EVIDENCE_LINE = re.compile(r"^\W*(verified|not verified|unverified|evidence|source|checked)\s*:", re.I | re.M)
EXACT_MARKER = re.compile(
    r"(?i)(?:\b(?:write|say|copy|use|reproduce|output|print|reply|respond|answer|quote|type|paste|keep|make)\s+"
    r"(?:(?:this|the following|it|that|the)\s+)?"
    r"(?:exactly|verbatim|word for word|character for character|as written|exact)\b"
    r"|\b(?:exactly|verbatim|word for word|character for character|as written)\s+"
    r"(?:this|the following|as follows|below)(?:\s+(?:text|wording|phrase|string|sentence))?\b)")
VERBATIM_DIRECTIVE = re.compile(
    r"(?i)\b(?:copy|write|say|use|quote|type|paste)\s+(?:this|the following)"
    r"(?:\s+(?:text|wording|phrase|string|sentence))?\s*:")
EXACT_TRAILER = re.compile(
    r"(?is)\b(?:exactly|verbatim|word for word|character for character|as written)\b[^\n:]*:\s*(.+)")
SOURCE_CLAIM = re.compile(
    r"(?i)https?://|\b(according to|the documentation|the docs|release notes|latest version|as of my knowledge|"
    r"all tests? pass|no other (call sites?|usages?|places?)|the only (place|caller|implementation)|"
    r"always (returns|happens)|never (happens|occurs|returns)|I (checked|verified|ran))\b|\bv?\d+\.\d+\.\d+\b")
OPEN_ITEM = re.compile(r"^\s*-\s*\[ \]\s*(.*)$", re.M)
PROMISE_START = re.compile(
    r"^\W*(i'll now|i will now|i('ll| will) (now|go ahead)|next,? i('ll| will)|now i('ll| will)|"
    r"let me (go ahead|now)|shall i (go ahead|proceed|continue|implement|fix|start|run)|"
    r"let me know if (you'?d|you would) like|would you like me to|want me to|"
    r"i can (also )?(do|make|add|run|fix) that|next steps\s*:)", re.I)
LEDGER_DIR = ".all-you-need"
MAX_ITEMS_SHOWN = 8

CHECK_MSG = ("Code was edited with no passing build, test, lint or type-check run after it. Run the project's "
             "declared checks and read the output, or say in the reply exactly which checks could not run and why.")
PROMISE_MSG = ("Your last paragraph is a plan or a promise for work you have not done. Do the work now, or state the "
               "concrete blocker that only the user can remove, then finish the turn with the result.")
SECURITY_MSG = ("Security-critical files were edited ({files}). End your reply with one line: `Security review needed: "
                "<what a human must review: authentication, authorization, crypto, secrets, permissions, deployment>`, "
                "or `Security review needed: none` if you checked each of those and nothing changed.")
HONESTY_MSG = ("Code was edited this turn. End your reply with one line: `Not verified: <what you skipped or could "
               "not check>`, or `Not verified: nothing` if every claim traces to something you ran or read.")
EXACT_MSG = ("The user asked for this text exactly and it does not appear verbatim in your reply: {text!r}. Reproduce "
             "it character for character, including punctuation, casing, spacing and order. Do not paraphrase, fix, "
             "shorten, translate or reformat it. If the exact text is impossible, name the constraint and ask; do not "
             "substitute another version.")
CLAIM_MSG = ("Your reply makes a source-sensitive claim (a URL, version, documentation reference, coverage claim or "
             "a statement that you checked something) without saying how it was checked. Verify it with a tool, then "
             "add one line: `Verified: <what you checked>` or `Not verified: <what you could not check>`. Do not label "
             "an unverified claim as verified.")


def edited_code(block: dict) -> bool:
    if block.get("name") not in EDIT_TOOLS:
        return False
    tool_input = block.get("input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    return Path(path).suffix.lower() in CODE_EXT


def ran_check(block: dict) -> bool:
    if block.get("name") == "Bash":
        command = block.get("input", {}).get("command", "") if isinstance(block.get("input"), dict) else ""
        if re.match(r"\s*echo\b", command):
            return False
        extra = os.environ.get(EXTRA_CHECK_ENV)
        return bool(CHECK_CMD.search(command)) or bool(extra and re.search(extra, command))
    return block.get("name") == "LSP"


def edited_path(block: dict) -> str:
    if block.get("name") not in EDIT_TOOLS:
        return ""
    tool_input = block.get("input")
    tool_input = tool_input if isinstance(tool_input, dict) else {}
    return tool_input.get("file_path") or tool_input.get("notebook_path") or ""


def exact_spans(user_text: str) -> list[str]:
    marker = EXACT_MARKER.search(user_text)
    directive = VERBATIM_DIRECTIVE.search(user_text)
    if not marker and not directive:
        return []
    fenced = [match.group(1).strip("\n") for match in re.finditer(r"```[^\n]*\n(.*?)```", user_text, re.S)]
    if fenced:
        return [span for span in fenced if len(span) >= 3]
    quoted = []
    for match in re.finditer(r'"([^"\n]{3,})"|“([^”\n]{3,})”|`([^`\n]{3,})`', user_text):
        quoted.append(next(group for group in match.groups() if group))
    if quoted:
        return quoted
    trailer = EXACT_TRAILER.search(user_text)
    if marker and trailer:
        tail = trailer.group(1)
    elif directive:
        tail = user_text[directive.end():]
    else:
        return []
    value = tail.splitlines()[0].strip().strip("'\"“”`")
    if len(value) < 3 or value.endswith("?"):
        return []
    return [value]


def exact_verdict(user_text: str, last_text: str) -> str | None:
    missing = [span for span in exact_spans(user_text) if span not in last_text]
    if not missing:
        return None
    return EXACT_MSG.format(text=missing[0][:300])


def claim_verdict(last_text: str) -> str | None:
    plain = re.sub(r"```.*?```", "", last_text, flags=re.S)
    if not SOURCE_CLAIM.search(plain) or EVIDENCE_LINE.search(last_text):
        return None
    return CLAIM_MSG


def entry_parts(entry: object) -> tuple[str, str | None, list[dict]]:
    if not isinstance(entry, dict):
        return "", None, []
    raw_kind = entry.get("type")
    kind = raw_kind if isinstance(raw_kind, str) else ""
    message = entry.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    blocks = [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []
    if kind != "user" or entry.get("isMeta"):
        return kind, None, blocks
    if isinstance(content, str):
        return kind, content, blocks
    if blocks and not any(b.get("type") == "tool_result" for b in blocks):
        texts = [b["text"] for b in blocks if b.get("type") == "text" and isinstance(b.get("text"), str)]
        return kind, "\n".join(texts), blocks
    return kind, None, blocks


def scan_turn(transcript: Path) -> tuple[bool, bool, str, list[str], str]:
    edited = pending = False
    paths: list[str] = []
    edits = 0
    running: dict[str, int] = {}                                                   
    last_text = ""
    user_text = ""
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:                               
            continue
        kind, prompt, content = entry_parts(entry)
        if prompt is not None:
            edited = pending = False
            paths = []
            running.clear()
            last_text = ""
            user_text = prompt
        elif kind == "user":
            for block in content:
                is_ok_check = (block.get("type") == "tool_result" and not block.get("is_error")
                               and running.pop(str(block.get("tool_use_id", "")), -1) == edits)
                if is_ok_check:
                    pending = False
        elif kind == "assistant":
            texts = [b.get("text", "") for b in content if b.get("type") == "text"]
            if texts:
                last_text = "\n".join(texts)
            for block in content:
                if block.get("type") != "tool_use":
                    continue
                if edited_path(block):
                    paths.append(edited_path(block))
                if edited_code(block):
                    edited = pending = True
                    edits += 1
                elif ran_check(block):
                    running[str(block.get("id", ""))] = edits
    return edited, pending, last_text, paths, user_text


def verdict(edited: bool, pending: bool, last_text: str, paths: list[str] | tuple = (),
            user_text: str = "") -> str | None:
    if edited and pending:
        return CHECK_MSG
    messages = []
    last_paragraph = [p for p in re.split(r"\n\s*\n", last_text.strip()) if p.strip()][-1:] or [""]
    if PROMISE_START.search(last_paragraph[0].strip()):
        messages.append(PROMISE_MSG)
    if edited and not VERIFIED_LINE.search(last_text):
        messages.append(HONESTY_MSG)
    exact = exact_verdict(user_text, last_text)
    if exact:
        messages.append(exact)
    claim = claim_verdict(last_text)
    if claim:
        messages.append(claim)
    critical = [p for p in paths if SECURITY_PATH.search(p)]
    if critical and not SECURITY_LINE.search(last_text):
        shown = ", ".join(dict.fromkeys(Path(p).name for p in critical))
        messages.append(SECURITY_MSG.format(files=shown))
    return "\n".join(messages) or None


def ledger_verdict(cwd: Path, stop_hook_active: bool) -> str | None:
    ledger = cwd / LEDGER_DIR / "tasks.md"
    state = cwd / LEDGER_DIR / ".stop-state.json"
    try:
        text = ledger.read_text(encoding="utf-8")
    except OSError:
        return None
    items = OPEN_ITEM.findall(text)
    if not items:
        state.unlink(missing_ok=True)
        return None
    try:
        previous = json.loads(state.read_text(encoding="utf-8"))["open"]
    except (OSError, ValueError, KeyError):
        previous = None
    if previous is not None and len(items) >= previous:
        return None                                                                               
    try:
        state.write_text(json.dumps({"open": len(items)}), encoding="utf-8")
    except OSError:
        if stop_hook_active:                                                           
            return None
    shown = "\n".join(f"- {item}" for item in items[:MAX_ITEMS_SHOWN])
    more = f"\n...and {len(items) - MAX_ITEMS_SHOWN} more" if len(items) > MAX_ITEMS_SHOWN else ""
    return (f"The task ledger ({LEDGER_DIR}/tasks.md) still has {len(items)} open item(s):\n{shown}{more}\n"
            "Continue with the first open item and tick each one as it is verified. If an item is truly blocked, mark "
            "it `- [!]` with the reason and report it. Do not stop with items silently open.")


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
    event = read_event()
    active = bool(event.get("stop_hook_active"))
    reason = ledger_verdict(Path(event.get("cwd") or os.getcwd()), active)
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))
        return
    if active:
        return
    transcript = Path(event.get("transcript_path", ""))
    if not transcript.is_file():
        return
    reason = verdict(*scan_turn(transcript))
    if reason:
        print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    main()
