#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

CATEGORIES = ("skills", "hooks", "commands", "agents", "tests", "docs", "memory", "security", "evals",
              "packaging", "installer", "hygiene", "ci")


def frontmatter(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    out: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            out[key.strip()] = value.strip().strip("'\"")
    return out


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def json_file(path: Path) -> dict:
    try:
        data = json.loads(read(path))
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def hook_scripts(hooks: dict) -> set[str]:
    found: set[str] = set()
    events = hooks.get("hooks")
    if not isinstance(events, dict):
        return found
    for handlers in events.values():
        if not isinstance(handlers, list):
            continue
        for group in handlers:
            for hook in (group.get("hooks") if isinstance(group, dict) else None) or []:
                command = hook.get("command", "") if isinstance(hook, dict) else ""
                found.update(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/([^\"'\s]+)", command))
    return found


class Audit:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[dict[str, str]] = []
        self.readme = read(root / "README.md")

    def find(self, category: str, severity: str, message: str) -> None:
        self.findings.append({"category": category, "severity": severity, "message": message})

    def skills(self) -> None:
        skills = sorted(p for p in (self.root / "skills").glob("*/SKILL.md"))
        if not skills:
            self.find("skills", "high", "no skills/*/SKILL.md files found")
            return
        for path in skills:
            meta = frontmatter(path)
            if meta.get("name") != path.parent.name:
                self.find("skills", "high", f"{path.relative_to(self.root)}: frontmatter name does not match directory")
            if len(meta.get("description", "")) < 40:
                self.find("skills", "medium", f"{path.relative_to(self.root)}: description is missing or too short")
            for ref in re.findall(r"`(references/[^`]+)`", read(path)):
                if (path.parent / ref).exists():
                    continue
                if not any((other.parent / ref).exists() for other in (self.root / "skills").glob("*/SKILL.md")):
                    self.find("skills", "medium", f"{path.relative_to(self.root)}: broken reference {ref}")

    def hooks(self) -> None:
        path = self.root / "hooks" / "hooks.json"
        data = json_file(path)
        if not data:
            self.find("hooks", "high", "hooks/hooks.json is missing or invalid")
            return
        events = data.get("hooks", {})
        for required in ("SessionStart", "PreToolUse", "PostToolUse", "Stop", "PreCompact"):
            if required not in events:
                self.find("hooks", "high", f"hooks.json does not wire {required}")
        for script in hook_scripts(data):
            if not (self.root / script).is_file():
                self.find("hooks", "high", f"hooks.json references missing script {script}")

    def commands(self) -> None:
        files = sorted((self.root / "commands").glob("*.md"))
        if len(files) < 3:
            self.find("commands", "medium", f"only {len(files)} command(s); expected at least 3")
        for path in files:
            meta = frontmatter(path)
            if not meta.get("description"):
                self.find("commands", "medium", f"{path.relative_to(self.root)}: missing description")

    def agents(self) -> None:
        files = sorted((self.root / "agents").glob("*.md"))
        if len(files) < 3:
            self.find("agents", "medium", f"only {len(files)} agent(s); expected at least 3")
        for path in files:
            meta = frontmatter(path)
            if meta.get("name") != path.stem:
                self.find("agents", "medium", f"{path.relative_to(self.root)}: name does not match file")
            if not meta.get("description"):
                self.find("agents", "medium", f"{path.relative_to(self.root)}: missing description")
            if not meta.get("tools"):
                self.find("agents", "low", f"{path.relative_to(self.root)}: no tools restriction")

    def tests(self) -> None:
        text = "\n".join(read(p) for p in (self.root / "tests").glob("test_*.py"))
        if not text:
            self.find("tests", "high", "no tests/test_*.py files")
            return
        units = list((self.root / "hooks").glob("*.py")) + list((self.root / "scripts").glob("*.py"))
        for unit in units:
            if unit.stem not in text:
                self.find("tests", "medium", f"no test mentions {unit.relative_to(self.root)}")
        if "unittest" not in text:
            self.find("tests", "low", "test suite does not use unittest")

    def docs(self) -> None:
        if not self.readme:
            self.find("docs", "high", "README.md missing")
            return
        for path in sorted((self.root / "skills").glob("*/SKILL.md")):
            if f"`{path.parent.name}`" not in self.readme:
                self.find("docs", "medium", f"README does not list skill {path.parent.name}")
        for path in sorted((self.root / "commands").glob("*.md")):
            if f"`/{path.stem}`" not in self.readme and f"`{path.stem}`" not in self.readme:
                self.find("docs", "medium", f"README does not list command {path.stem}")
        for path in sorted((self.root / "agents").glob("*.md")):
            if f"`{path.stem}`" not in self.readme:
                self.find("docs", "medium", f"README does not list agent {path.stem}")
        if "PreCompact" not in self.readme:
            self.find("docs", "low", "README does not explain the PreCompact checkpoint")

    def memory(self) -> None:
        session = read(self.root / "hooks" / "session_start.py")
        for token in ("checkpoint", "ledger", "lesson"):
            if token not in session.lower():
                self.find("memory", "high", f"session_start.py does not restore {token}")
        if not (self.root / "hooks" / "pre_compact.py").is_file():
            self.find("memory", "high", "no pre-compaction checkpoint writer")
        if "PreCompact" not in read(self.root / "hooks" / "hooks.json"):
            self.find("memory", "high", "PreCompact is not wired")

    def security(self) -> None:
        for name in ("guard_secrets.py", "guard_actions.py", "guard_config.py", "stop_gate.py"):
            if not (self.root / "hooks" / name).is_file():
                self.find("security", "high", f"missing guard hooks/{name}")
        if not (self.root / "scripts" / "security_scan.py").is_file():
            self.find("security", "high", "missing scripts/security_scan.py")
        wired = hook_scripts(json_file(self.root / "hooks" / "hooks.json"))
        dispatcher = read(self.root / "hooks" / "pre_tool.py") if "hooks/pre_tool.py" in wired else ""
        for name in ("hooks/guard_secrets.py", "hooks/guard_actions.py", "hooks/guard_config.py"):
            module = name.rsplit("/", 1)[-1][:-3]
            if name not in wired and f"import {module}" not in dispatcher:
                self.find("security", "high", f"{name} is not wired in hooks.json")
        if "--dangerously-skip-permissions" in self.readme or "Bash(*)" in read(self.root / "templates" / "settings.json"):
            self.find("security", "high", "README or settings template recommends a bypass or wildcard permission")

    def evals(self) -> None:
        if not (self.root / "scripts" / "run_evals.py").is_file():
            self.find("evals", "medium", "missing scripts/run_evals.py")
        if not (self.root / "evals" / "scenarios.md").is_file():
            self.find("evals", "medium", "missing evals/scenarios.md")

    def packaging(self) -> None:
        plugin = json_file(self.root / ".claude-plugin" / "plugin.json")
        if not plugin:
            self.find("packaging", "high", ".claude-plugin/plugin.json missing or invalid")
            return
        for key in ("name", "version", "description", "author", "icon"):
            if not plugin.get(key):
                self.find("packaging", "medium", f"plugin.json has no {key}")
        icon = plugin.get("icon", "")
        if icon.startswith("./"):
            icon = icon[2:]
        if icon and not (self.root / icon).is_file():
            self.find("packaging", "high", f"plugin icon {icon} does not exist")
        if not json_file(self.root / ".claude-plugin" / "marketplace.json"):
            self.find("packaging", "medium", "marketplace.json missing or invalid")

    def installer(self) -> None:
        script = self.root / "install.sh"
        if not script.is_file():
            self.find("installer", "high", "install.sh missing")
            return
        try:
            result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.SubprocessError):
            self.find("installer", "medium", "could not parse install.sh")
            return
        if result.returncode != 0:
            self.find("installer", "high", f"install.sh has a syntax error: {result.stderr.strip()[:160]}")

    def hygiene(self) -> None:
        junk = [p for p in self.root.rglob("*") if p.name in {".DS_Store", "Thumbs.db"} or p.suffix == ".pyc"]
        junk += [p for p in self.root.rglob("__pycache__") if p.is_dir()]
        if junk:
            self.find("hygiene", "medium", f"{len(junk)} cache or OS file(s) in the tree; remove before release")
        ignore = read(self.root / ".gitignore")
        for token in (".DS_Store", "__pycache__/", ".all-you-need/"):
            if token not in ignore:
                self.find("hygiene", "low", f".gitignore does not cover {token}")
        core = read(self.root / "hooks" / "core-rules.md")
        if len(core.split()) > 250:
            self.find("hygiene", "medium", f"hooks/core-rules.md has {len(core.split())} words; the session-start core should stay at or below 250")
        skill_rows = re.findall(r"^\| Skill `([^`]+)`", self.readme, re.M)
        for duplicate in sorted({name for name in skill_rows if skill_rows.count(name) > 1}):
            self.find("docs", "low", f"README lists skill {duplicate} more than once")

    def ci(self) -> None:
        workflows = list((self.root / ".github" / "workflows").glob("*.yml")) + \
            list((self.root / ".github" / "workflows").glob("*.yaml"))
        if not workflows:
            self.find("ci", "medium", "no CI workflow")
            return
        text = "\n".join(read(p) for p in workflows)
        if "unittest" not in text:
            self.find("ci", "medium", "CI does not run the unit tests")
        if "security_scan" not in text:
            self.find("ci", "low", "CI does not run the security scanner")
        if "harness_audit" not in text:
            self.find("ci", "low", "CI does not run the harness audit")

    def run(self) -> dict:
        for name in CATEGORIES:
            getattr(self, name)()
        return {"findings": self.findings,
                "counts": {level: sum(1 for f in self.findings if f["severity"] == level)
                           for level in ("high", "medium", "low")}}


def render(result: dict) -> str:
    lines = ["Static structure and wiring checks (does not measure model output quality):"]
    findings = result["findings"]
    if not findings:
        lines.append("All configured checks passed.")
    else:
        lines.append(f"Findings: {result['counts']['high']} high, {result['counts']['medium']} medium, "
                     f"{result['counts']['low']} low")
        for finding in findings:
            lines.append(f"  [{finding['severity']}] {finding['category']}: {finding['message']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check static harness completeness and wiring; not model output quality.")
    parser.add_argument("--root", default=".", help="repository root (default: .)")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    result = Audit(Path(args.root).resolve()).run()
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(render(result))
    return 1 if result["counts"]["high"] else 0


if __name__ == "__main__":
    sys.exit(main())
