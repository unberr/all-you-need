#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

TS_EXT = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".vue", ".svelte", ".astro"}
PY_EXT = {".py"}
C_EXT = {".c", ".h", ".cc", ".cpp", ".hpp"}
RS_EXT = {".rs"}
GO_EXT = {".go"}
CS_EXT = {".cs"}
PHP_EXT = {".php"}
HTML_EXT = {".html", ".htm"}
CSS_EXT = {".css", ".scss", ".less"}
OTHER_CODE_EXT = {".swift", ".kt", ".java", ".rb", ".sh", ".zsh", ".sql"}
CODE_EXT = TS_EXT | PY_EXT | C_EXT | RS_EXT | GO_EXT | CS_EXT | PHP_EXT | HTML_EXT | CSS_EXT | OTHER_CODE_EXT
NO_EMOJI_CHECK = HTML_EXT | CSS_EXT                                        
DECORATIVE = re.compile("[─-╿←-⇿‒-―]")                                           
VAGUE_FILENAME = re.compile(r"(^|[\\/])(utils?|helpers?|common|misc)\.\w+$", re.I)

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⭕]")
TEST_PATH = re.compile(r"(^|[\\/])(tests?|__tests__|specs?|fixtures?)[\\/]|(_test|\.test|\.spec)\.\w+$|(^|[\\/])test_[^\\/]*$")

                                                     
QUALITY_RULES = [
    (TS_EXT, re.compile(r":\s*any\b|\bas any\b|<any>"), "uses `any`: type it properly or use `unknown` and narrow"),
    (TS_EXT, re.compile(r"@ts-ignore|@ts-nocheck"), "suppresses the type checker: fix the type"),
    (TS_EXT, re.compile(r"catch\s*(\([^)]*\))?\s*\{\s*\}"), "empty catch swallows the error: handle the specific failure"),
    (PY_EXT, re.compile(r"#\s*type:\s*ignore"), "suppresses the type checker: fix the type"),
    (PY_EXT, re.compile(r"^\s*except\s*(Exception)?\s*:\s*(pass)?\s*$", re.M), "bare or broad except: catch the specific failure"),
    (PY_EXT, re.compile(r"except[^\n]*:\s*\n\s*pass\b"), "except-pass swallows the error"),
    (TS_EXT, re.compile(r"\bvar\s+[A-Za-z_$]"), "var: use const or let"),
    (PY_EXT, re.compile(r"def\s+\w+\([^)]*=\s*(\[\]|\{\}|set\(\))"), "mutable default argument: default to None and create inside"),
    (PY_EXT, re.compile(r"^\s*from\s+\S+\s+import\s+\*", re.M), "import *: import the names you use"),
    (CS_EXT, re.compile(r"catch\s*(\(\s*Exception[^)]*\))?\s*\{\s*\}"), "empty catch swallows the error: handle the specific failure"),
    (CS_EXT, re.compile(r"\basync\s+void\b"), "async void: use async Task unless this is an event handler"),
    (CS_EXT, re.compile(r"\.GetAwaiter\(\)\.GetResult\(\)|\.Wait\(\)"), "blocking on async work: await it"),
    (HTML_EXT, re.compile(r"<img\b(?![^>]*\balt=)[^>]*>", re.I), "img without alt: add meaningful alt text, or alt=\"\" if decorative"),
    (HTML_EXT, re.compile(r"\son(click|change|submit|load|error|input)\s*=", re.I), "inline event handler: attach it in script (keeps a strict CSP possible)"),
    (HTML_EXT, re.compile(r"<a\b[^>]*href=[\"']#[\"']", re.I), "link to # used as a button: use a <button>"),
    (HTML_EXT, re.compile(r"user-scalable\s*=\s*no|maximum-scale\s*=\s*1\b", re.I), "blocks pinch zoom: remove it"),
    (HTML_EXT, re.compile(r"<a\b(?=[^>]*target=[\"']_blank[\"'])(?![^>]*\brel=)[^>]*>", re.I), "target=_blank without rel=noopener"),
    (CSS_EXT, re.compile(r"outline\s*:\s*(none|0)\b"), "focus outline removed: style :focus-visible instead of hiding it"),
    (CSS_EXT, re.compile(r"!important"), "!important: lower specificity or use @layer instead"),
    (CSS_EXT, re.compile(r"z-index\s*:\s*\d{4,}"), "huge z-index: use a named z-index scale"),
    (None, re.compile(r"(?i)rest of (the )?(code|file|function|class|implementation)|existing code (here|remains|goes here)|your (code|implementation|logic) (goes )?here|(add|implement) (the )?(logic|code|implementation) here"), "placeholder comment: write the real code"),
    (None, re.compile(r"\bassert True\b|expect\(\s*true\s*\)\.toBe\(\s*true\s*\)|assertTrue\(\s*True\s*\)|\bassert 1 == 1\b"), "test that cannot fail: assert the real behavior"),
    (None, re.compile(r"@pytest\.mark\.skip|\b(xit|xdescribe|xtest)\(|\b(it|test|describe)\.skip\(|\bt\.Skip\(|@Ignore\b|\[Ignore\]|markTestSkipped|#\[ignore\]"), "skipped test: fix the code or the test, or report it, do not hide it"),
    (TS_EXT, re.compile(r"\bdebugger\b\s*;?|console\.(log|debug)\("), "debug output left in code: remove it"),
    (PY_EXT, re.compile(r"\bbreakpoint\(\)|pdb\.set_trace\(\)|^\s*import pdb\b", re.M), "debugger call left in code: remove it"),
    (RS_EXT, re.compile(r"\bdbg!\("), "dbg! left in code: remove it"),
    (None, re.compile(r"(?m)^\s*(//|#|--)\s*(changed|fixed|updated|added|removed|note:? this (used|was)|per (the )?(request|ticket|review)|now (uses|returns)|new code|old code)\b"), "comment narrates the change: put it in the commit message, not the source"),
    (None, re.compile(r"(?m)^\s*(//|#|--|/\*)\s*[-=*#~_]{4,}"), "banner comment: split the code or rename instead"),
    (None, re.compile(r"(?m)^\s*(//|#)\s*(increment|decrement|loop (over|through)|return the|set the|get the|create (a|the)|initiali[sz]e)\b"), "comment restates the next line: delete it and name the code better"),
    (None, re.compile(r"\b(TODO|FIXME|XXX)\b"), "TODO/FIXME left in code: finish it or drop it"),
    (None, re.compile(r"NotImplemented(Error)?\b|unimplemented!\s*\(|todo!\s*\("), "stub left in code: implement it or remove the path"),
]

SECURITY_RULES = [
    (PY_EXT, re.compile(r"shell\s*=\s*True"), "shell=True: pass an argument list instead (command injection)"),
    (PY_EXT, re.compile(r"\bpickle\.loads?\(|\byaml\.load\((?![^)]*SafeLoader)"), "unsafe deserialization: use a safe format or loader"),
    (PY_EXT, re.compile(r"verify\s*=\s*False"), "TLS verification disabled: keep certificate checks on"),
    (TS_EXT, re.compile(r"\beval\s*\(|new Function\s*\(|\binnerHTML\s*=|dangerouslySetInnerHTML"), "code or HTML injection sink: avoid it or encode the input"),
    (TS_EXT, re.compile(r"rejectUnauthorized\s*:\s*false"), "TLS verification disabled: keep certificate checks on"),
    (C_EXT, re.compile(r"\b(gets|strcpy|strcat|sprintf|vsprintf)\s*\(|scanf\s*\(\s*\"[^\"]*%s"), "unbounded C string function: use snprintf, strnlen and bounded copies"),
    (GO_EXT, re.compile(r"InsecureSkipVerify\s*:\s*true"), "TLS verification disabled: keep certificate checks on"),
    (GO_EXT, re.compile(r"exec\.Command\(\s*\"(sh|bash)\"\s*,\s*\"-c\""), "shell command string: pass an argument list instead (command injection)"),
    (CS_EXT, re.compile(r"\bBinaryFormatter\b"), "BinaryFormatter is unsafe deserialization: use System.Text.Json"),
    (PHP_EXT, re.compile(r"\beval\s*\(|\bunserialize\s*\(|\bextract\s*\(\s*\$_|\bmysql_query\s*\("), "unsafe PHP function: avoid eval, unserialize on input, extract on request data and mysql_*"),
    (PHP_EXT, re.compile(r"(query|exec)\s*\(\s*\"[^\"]*\$\w+"), "SQL with interpolated variable: use prepared statements"),
    (None, re.compile(r"\b(md5|sha1)\b\s*\(|hashlib\.(md5|sha1)\b", re.I), "MD5/SHA-1: not for passwords or integrity; use a modern hash"),
    (None, re.compile(r"(?i)(execute|query)\s*\(\s*(f[\"']|[\"'][^\"']*[\"']\s*(\+|%|\.format))"), "SQL built by string formatting: use parameterized queries"),
    (None, re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token)\b\s*[:=]\s*[\"'][^\"'\s]{8,}[\"']"), "possible hardcoded secret: read it from the environment"),
]


def rust_findings(text: str, test_path: bool) -> list[str]:
    out = []
    for m in re.finditer(r"\bunsafe\s*(\{|fn\b|impl\b)", text):
        if "SAFETY" not in text[max(0, m.start() - 300):m.start()]:
            out.append("unsafe without a `// SAFETY:` comment stating why it is sound")
            break
    if ".unwrap()" in text and not test_path and "#[cfg(test)]" not in text:
        out.append("unwrap() outside tests: propagate with ? or use expect() naming the invariant")
    return out


def added_text(tool_name: str, tool_input: dict) -> str:
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name == "Edit":
        return tool_input.get("new_string", "")
    if tool_name == "MultiEdit":
        return "\n".join(e.get("new_string", "") for e in tool_input.get("edits", []))
    return ""


def findings(path: str, text: str) -> list[str]:
    ext = Path(path).suffix.lower()
    if ext not in CODE_EXT:
        return []
    test_path = bool(TEST_PATH.search(path))
    rules = QUALITY_RULES if test_path else QUALITY_RULES + SECURITY_RULES
    out = []
    for exts, pattern, message in rules:
        if exts is not None and ext not in exts:
            continue
        match = pattern.search(text)
        if match:
            out.append(f"{message} (`{match.group(0).strip()[:40]}`)")
    if ext in RS_EXT:
        out += rust_findings(text, test_path)
    if ext not in NO_EMOJI_CHECK and EMOJI.search(text):
        out.append("emoji in code or logs: remove it")
    if ext not in NO_EMOJI_CHECK and DECORATIVE.search(text):
        out.append("decorative unicode (box drawing, arrows, typographic dashes) in source: use plain ASCII")
    if VAGUE_FILENAME.search(path):
        out.append("file named utils/helpers/common/misc: name the module for what it does")
    return out


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
    event = read_event()
    tool_input = event.get("tool_input") or {}
    path = tool_input.get("file_path", "")
    found = findings(path, added_text(event.get("tool_name", ""), tool_input))
    if not found:
        return
    note = f"all-you-need quality check on {path}:\n- " + "\n- ".join(found) + "\nFix these in your next edit unless the user asked for them."
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}}))


if __name__ == "__main__":
    main()
