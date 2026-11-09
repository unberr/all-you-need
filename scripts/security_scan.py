#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITY_WEIGHT = {"critical": 25, "high": 12, "medium": 5, "low": 2}
PATTERN_FILES = {"guard_actions.py", "guard_secrets.py", "slop_lint.py", "harness_audit.py", "security_scan.py"}
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "tests", "evals", ".all-you-need"}

SECRETS = [
    ("private-key", "critical", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
     "private key material in the repository"),
    ("aws-key", "critical", re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS access key id"),
    ("github-token", "critical", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b"), "GitHub token"),
    ("slack-token", "critical", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "Slack token"),
    ("generic-secret", "high",
     re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd|client_secret)\b\s*[:=]\s*[\"']([A-Za-z0-9_\-./+=]{24,})[\"']"),
     "hardcoded credential-like value"),
]

CODE = [
    ("pipe-to-shell", "critical", re.compile(r"\b(?:curl|wget)\b[^|\n;]*\|\s*(?:sudo\s+)?(?:ba|z|da)?sh\b"),
     "pipes a remote script into a shell"),
    ("bypass-permissions", "critical", re.compile(r"(?i)--dangerously-skip-permissions|\bbypassPermissions\b"),
     "bypasses the permission system"),
    ("world-writable", "high", re.compile(r"\bchmod\s+(?:-R\s+)?777\b"), "makes files world-writable"),
    ("shell-true", "high", re.compile(r"subprocess\.[A-Za-z_]+\([^)\n]*shell\s*=\s*True"),
     "runs a shell with interpolated input"),
    ("tls-verify-off", "high", re.compile(r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false"), "disables TLS verification"),
    ("os-system", "medium", re.compile(r"\bos\.system\s*\("), "uses os.system instead of an argument list"),
    ("pickle", "medium", re.compile(r"\bpickle\.loads?\s*\("), "deserializes untrusted pickle data"),
    ("unsafe-yaml", "medium", re.compile(r"\byaml\.load\s*\((?![^)\n]*SafeLoader)"), "yaml.load without SafeLoader"),
    ("eval", "medium", re.compile(r"(?<![.\w])eval\s*\("), "evaluates a string as code"),
    ("unpinned-npx", "medium", re.compile(r"\bnpx\s+(?:--yes|-y\s+)?([@A-Za-z0-9._/-]+)"), "runs an npx package"),
    ("plain-http", "low", re.compile(r"http://(?!localhost|127\.0\.0\.1|\[::1\])[A-Za-z0-9.-]+"),
     "uses an unencrypted HTTP endpoint"),
]

INJECTION = [
    ("instruction-override", "high",
     re.compile(r"(?im)^\s*(?:ignore|disregard|forget)\b[^\n]{0,50}\b(?:instructions?|rules?|prompts?)\b"),
     "tells the agent to ignore higher-priority instructions"),
    ("secret-exfiltration", "high",
     re.compile(r"(?im)^\s*(?:reveal|print|output|send|post|upload)\b[^\n]{0,60}\b(?:" "secrets?|credentials?|tokens?|api[ _-]?keys?|system prompt)\b"),
     "tells the agent to disclose secrets or its instructions"),
    ("role-hijack", "medium",
     re.compile(r"(?im)^\s*(?:you are now|from now on,? you (?:are|will|must))\b"),
     "reassigns the agent's role"),
]

SETTINGS = [
    ("wildcard-bash", "critical", re.compile(r"\"Bash\(\*\)\""), "allows every shell command"),
    ("bypass-mode", "critical", re.compile(r"\"defaultMode\"\s*:\s*\"bypassPermissions\"|\"bypassPermissions\"\s*:\s*true"),
     "enables bypass permissions"),
]


def iter_files(root: Path) -> list[Path]:
    patterns = ["hooks/*.py", "hooks/*.json", "hooks/*.md", "scripts/*.py", "scripts/*.sh", "commands/*.md",
                "agents/*.md", "skills/*/SKILL.md", ".claude-plugin/*.json", "templates/*.json"]
    files: list[Path] = []
    for pattern in patterns:
        files.extend(p for p in root.glob(pattern) if p.is_file())
    return sorted(set(files))


def secret_value_is_safe(value: str) -> bool:
    low = value.lower()
    return any(token in low for token in ("${", "os.environ", "process.env", "example", "placeholder", "your_",
                                           "changeme", "xxxx", "...", "<", ">"))


def scan_file(path: Path, root: Path) -> list[dict]:
    findings: list[dict] = []
    try:
        text = path.read_text(encoding="utf-8")
        rel = str(path.relative_to(root))
    except (OSError, UnicodeDecodeError):
        return findings
    code_like = path.suffix in {".py", ".sh", ".js", ".ts", ".json"}
    pattern_file = path.name in PATTERN_FILES
    for number, line in enumerate(text.splitlines(), 1):
        for rule, severity, regex, message in SECRETS:
            for match in regex.finditer(line):
                value = match.group(2) if rule == "generic-secret" else match.group(0)
                if rule == "generic-secret" and secret_value_is_safe(value):
                    continue
                findings.append({"rule": rule, "severity": severity, "path": rel, "line": number,
                                 "text": line.strip()[:160], "message": message})
        if code_like and not pattern_file:
            for rule, severity, regex, message in CODE:
                match = regex.search(line)
                if not match:
                    continue
                if rule == "unpinned-npx":
                    package = match.group(1)
                    if "@" in package.lstrip("@") or package.startswith("."):
                        continue
                findings.append({"rule": rule, "severity": severity, "path": rel, "line": number,
                                 "text": line.strip()[:160], "message": message})
    if path.suffix == ".md" or path.name == "core-rules.md":
        for number, line in enumerate(text.splitlines(), 1):
            for rule, severity, regex, message in INJECTION:
                if regex.search(line):
                    findings.append({"rule": rule, "severity": severity, "path": rel, "line": number,
                                     "text": line.strip()[:160], "message": message})
    if path.parent.name == "templates" and path.suffix == ".json":
        parsed = {}
        try:
            parsed = json.loads(text)
        except ValueError:
            pass
        if parsed:
            for rule, severity, regex, message in SETTINGS:
                if regex.search(text):
                    findings.append({"rule": rule, "severity": severity, "path": rel, "line": 0,
                                     "text": "", "message": message})
            permissions = parsed.get("permissions", {}) if isinstance(parsed.get("permissions"), dict) else {}
            if not permissions.get("deny"):
                findings.append({"rule": "no-deny-rules", "severity": "low", "path": rel, "line": 0, "text": "",
                                 "message": "permission template has no deny rules"})
            if not parsed.get("sandbox"):
                findings.append({"rule": "no-sandbox", "severity": "low", "path": rel, "line": 0, "text": "",
                                 "message": "permission template does not enable the sandbox"})
    return findings


def dedupe(findings: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    out: list[dict] = []
    for finding in findings:
        key = (finding["rule"], finding["path"], finding["line"])
        if key not in seen:
            seen.add(key)
            out.append(finding)
    return sorted(out, key=lambda f: (-SEVERITY_WEIGHT[f["severity"]], f["path"], f["line"]))


def grade(score: int) -> str:
    return "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 70 else "D" if score >= 60 else "F"


def run(root: Path) -> dict:
    findings = dedupe([finding for path in iter_files(root) for finding in scan_file(path, root)])
    counts = {level: sum(1 for f in findings if f["severity"] == level)
              for level in ("critical", "high", "medium", "low")}
    score = max(0, 100 - sum(SEVERITY_WEIGHT[f["severity"]] for f in findings))
    return {"score": score, "grade": grade(score), "counts": counts, "findings": findings,
            "files_scanned": len(iter_files(root))}


def render(result: dict) -> str:
    lines = [f"Security scan: {result['score']}/100 (grade {result['grade']}, {result['files_scanned']} files)",
             f"Findings: {result['counts']['critical']} critical, {result['counts']['high']} high, "
             f"{result['counts']['medium']} medium, {result['counts']['low']} low"]
    for finding in result["findings"]:
        location = f"{finding['path']}:{finding['line']}" if finding["line"] else finding["path"]
        lines.append(f"  [{finding['severity']}] {finding['rule']} at {location}: {finding['message']}")
        if finding["text"]:
            lines.append(f"      {finding['text']}")
    if not result["findings"]:
        lines.append("No findings. This is a pattern scan, not a proof: review the surfaces you changed.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan harness surfaces for security problems.")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    result = run(Path(args.root).resolve())
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 1 if result["counts"]["critical"] or result["counts"]["high"] else 0


if __name__ == "__main__":
    sys.exit(main())
