#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

try:
    import tomllib
except ImportError:                                                     
    tomllib = None

OSV_BATCH_URL = "https://api.osv.dev/v1/querybatch"
TIMEOUT_SECONDS = 8
BATCH_SIZE = 500
MAX_DEPS = 2000
MAX_IDS_SHOWN = 5
MANIFESTS = {"requirements.txt", "package.json", "cargo.toml", "go.mod"}

REGISTRY_TIMEOUT_SECONDS = 5
MAX_REGISTRY_LOOKUPS = 60
YOUNG_DAYS = 30
COPYLEFT = re.compile(r"\b(A?GPL|LGPL|SSPL|EUPL|CC-BY-SA)\b", re.I)
USER_AGENT = "all-you-need-supply-chain-check"

Dep = tuple[str, str, str]                                          
Name = tuple[str, str]                                 


def parse_requirements(text: str) -> list[Dep]:
    pattern = re.compile(r"^\s*([A-Za-z0-9_.\-]+)(?:\[[^\]]*\])?\s*==\s*([A-Za-z0-9_.+\-]+)")
    return [("PyPI", m[1], m[2]) for line in text.splitlines() if (m := pattern.match(line))]


def _json(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:                                                     
        return {}
    return data if isinstance(data, dict) else {}


def _toml_subset(text: str) -> dict:
    packages: list[dict] = []
    sections: dict[str, dict] = {}
    section, current = "", None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "[[package]]":
            current = {}
            packages.append(current)
            section = "[[package]]"
            continue
        header = re.match(r"^\[([^\[\]]+)\]$", stripped)
        if header:
            section, current = header.group(1).strip(), None
            continue
        if stripped.startswith("[["):
            section, current = "", None
            continue
        pair = re.match(r"^([A-Za-z0-9_.\-]+)\s*=\s*(.+)$", stripped)
        if not pair:
            continue
        key, value = pair.groups()
        if section == "[[package]]" and current is not None:
            quoted = re.match(r'^"([^"]*)"', value)
            if key in ("name", "version", "source") and quoted and key not in current:
                current[key] = quoted.group(1)
        elif section in ("dependencies", "dev-dependencies", "build-dependencies"):
            if value.startswith('"'):
                sections.setdefault(section, {})[key] = re.match(r'^"([^"]*)"', value).group(1)
            elif value.startswith("{"):
                spec: dict = {}
                version = re.search(r'\bversion\s*=\s*"([^"]*)"', value)
                if version:
                    spec["version"] = version.group(1)
                for marker in ("path", "git"):
                    if re.search(rf"\b{marker}\s*=", value):
                        spec[marker] = True
                sections.setdefault(section, {})[key] = spec
    return {"package": [p for p in packages if p], **sections}


def _toml(text: str) -> dict:
    if tomllib is None:
        return _toml_subset(text)
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return {}


def parse_package_json(text: str) -> list[Dep]:
    data = _json(text)
    deps: list[Dep] = []
    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        for name, spec in (data.get(section) or {}).items():
            m = re.fullmatch(r"[\^~=v]*(\d+(?:\.\d+){0,2}(?:-[\w.]+)?)", str(spec).strip())
            if m:
                deps.append(("npm", name, m[1]))
    return deps


def parse_package_lock(text: str) -> list[Dep]:
    data = _json(text)
    deps: list[Dep] = []
    for key, info in (data.get("packages") or {}).items():                           
        if key and isinstance(info, dict) and info.get("version") and not info.get("link"):
            deps.append(("npm", key.rsplit("node_modules/", 1)[-1], info["version"]))
    if not deps:                     
        for name, info in (data.get("dependencies") or {}).items():
            if isinstance(info, dict) and info.get("version"):
                deps.append(("npm", name, info["version"]))
    return deps


def parse_pipfile_lock(text: str) -> list[Dep]:
    data = _json(text)
    deps: list[Dep] = []
    for section in ("default", "develop"):
        for name, info in (data.get(section) or {}).items():
            version = str((info or {}).get("version", "")).lstrip("=")
            if version:
                deps.append(("PyPI", name, version))
    return deps


def parse_cargo_toml(text: str) -> list[Dep]:
    data = _toml(text)
    deps: list[Dep] = []
    for section in ("dependencies", "dev-dependencies", "build-dependencies"):
        for name, spec in (data.get(section) or {}).items():
            version = spec if isinstance(spec, str) else (spec.get("version") if isinstance(spec, dict) else None)
            m = re.fullmatch(r"[\^~=]*(\d+(?:\.\d+){0,2})", str(version or "").strip())
            if m:
                deps.append(("crates.io", name, m[1]))
    return deps


def parse_cargo_lock(text: str) -> list[Dep]:
                                                                                     
    return [("crates.io", p["name"], p["version"]) for p in _toml(text).get("package", [])
            if p.get("source") and p.get("name") and p.get("version")]


def parse_python_toml_lock(text: str) -> list[Dep]:                           
    return [("PyPI", p["name"], p["version"]) for p in _toml(text).get("package", [])
            if p.get("name") and p.get("version")]


def parse_go_mod(text: str) -> list[Dep]:
    pattern = re.compile(r"^\s*(?:require\s+)?([\w.\-/]+\.[\w.\-/]+)\s+v(\d[\w.+\-]*)\s*(?://.*)?$")
    return [("Go", m[1], m[2]) for line in text.splitlines() if (m := pattern.match(line))]


def parse_go_sum(text: str) -> list[Dep]:
    deps: list[Dep] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1].startswith("v") and not parts[1].endswith("/go.mod"):
            deps.append(("Go", parts[0], parts[1][1:]))
    return deps


PARSERS = {
    "requirements.txt": parse_requirements,
    "package.json": parse_package_json,
    "package-lock.json": parse_package_lock,
    "pipfile.lock": parse_pipfile_lock,
    "cargo.toml": parse_cargo_toml,
    "cargo.lock": parse_cargo_lock,
    "poetry.lock": parse_python_toml_lock,
    "uv.lock": parse_python_toml_lock,
    "go.mod": parse_go_mod,
    "go.sum": parse_go_sum,
}


def query_osv(deps: list[Dep]) -> list[list[str]]:
    advisories: list[list[str]] = []
    for start in range(0, len(deps), BATCH_SIZE):
        chunk = deps[start:start + BATCH_SIZE]
        queries = [{"package": {"name": name, "ecosystem": eco}, "version": version} for eco, name, version in chunk]
        request = urllib.request.Request(OSV_BATCH_URL, data=json.dumps({"queries": queries}).encode(),
                                         headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:                              
            results = json.load(response)["results"]
        if len(results) != len(chunk):
            raise ValueError("OSV returned a result count that does not match the query")
        advisories += [[v["id"] for v in (r.get("vulns") or [])] for r in results]
    return advisories


def declared_names(filename: str, text: str) -> list[Name]:
    names: list[Name] = []
    lowered = filename.lower()
    if lowered == "requirements.txt":
        for line in text.splitlines():
            m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9_.\-]*)(?:\[[^\]]*\])?\s*(?:$|[=<>!~;#])", line)
            if m:
                names.append(("PyPI", m[1]))
    elif lowered == "package.json":
        data = _json(text)
        for section in ("dependencies", "devDependencies", "optionalDependencies"):
            for name, spec in (data.get(section) or {}).items():
                if not re.match(r"(git|https?:|file:|link:|workspace:|github:|npm:)|/", str(spec)) or re.match(r"[\^~>=<*\d]", str(spec)):
                    names.append(("npm", name))
    elif lowered == "cargo.toml":
        data = _toml(text)
        for section in ("dependencies", "dev-dependencies", "build-dependencies"):
            for name, spec in (data.get(section) or {}).items():
                if isinstance(spec, str) or (isinstance(spec, dict) and "path" not in spec and "git" not in spec):
                    names.append(("crates.io", spec.get("package", name) if isinstance(spec, dict) else name))
    elif lowered == "go.mod":
        names = [("Go", d[1]) for d in parse_go_mod(text)]
    return list(dict.fromkeys(names))


def _go_escape(module: str) -> str:
    return re.sub(r"[A-Z]", lambda m: "!" + m[0].lower(), module)


def registry_url(eco: str, name: str) -> str:
    if eco == "PyPI":
        return f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json"
    if eco == "npm":
        return f"https://registry.npmjs.org/{urllib.parse.quote(name, safe='@')}/latest"
    if eco == "crates.io":
        return f"https://crates.io/api/v1/crates/{urllib.parse.quote(name)}"
    return f"https://proxy.golang.org/{_go_escape(name)}/@v/list"


def fetch_registry(url: str) -> dict | None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REGISTRY_TIMEOUT_SECONDS) as response:                                
            body = response.read()
    except urllib.error.HTTPError as error:
        if error.code in (404, 410):
            return None
        raise
    try:
        data = json.loads(body)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _age_days(timestamp: str | None) -> int | None:
    if not timestamp:
        return None
    try:
        created = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - created).days


def registry_issues(eco: str, name: str, data: dict | None) -> list[str]:
    if data is None:
        return [f"{name}: NOT FOUND in the {eco} registry. It may be a hallucinated or mistyped name: do not install it"]
    issues: list[str] = []
    license_text, created = "", None
    if eco == "PyPI":
        info = data.get("info") or {}
        license_text = str(info.get("license_expression") or info.get("license") or "")[:200]
        uploads = [f.get("upload_time_iso_8601") for files in (data.get("releases") or {}).values() for f in files]
        created = min((u for u in uploads if u), default=None)
    elif eco == "npm":
        license_value = data.get("license")
        license_text = str(license_value.get("type") if isinstance(license_value, dict) else license_value or "")
    elif eco == "crates.io":
        crate = data.get("crate") or {}
        created = crate.get("created_at")
        versions = data.get("versions") or [{}]
        license_text = str(versions[0].get("license") or "")
    age = _age_days(created)
    if age is not None and age < YOUNG_DAYS:
        issues.append(f"{name}: first published only {age} day(s) ago; verify it is the package you intend (typosquat risk)")
    if license_text and COPYLEFT.search(license_text):
        issues.append(f"{name}: license {license_text.strip()[:60]!r} is copyleft; check it fits the project's license")
    return issues


def unpinned(filename: str, text: str) -> list[str]:
    lowered = filename.lower()
    found: list[str] = []
    if lowered == "requirements.txt":
        for line in text.splitlines():
            m = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9_.\-]*)(?:\[[^\]]*\])?\s*(?:$|[<>!~;#]|>=)", line)
            if m and "==" not in line and not line.lstrip().startswith("-"):
                found.append(m[1])
    elif lowered == "package.json":
        data = _json(text)
        for section in ("dependencies", "devDependencies", "optionalDependencies"):
            for name, spec in (data.get(section) or {}).items():
                if str(spec).strip() in ("*", "latest", "", "x") or str(spec).startswith((">", "<")):
                    found.append(f"{name}@{spec or 'empty'}")
    elif lowered == "cargo.toml":
        for section in ("dependencies", "dev-dependencies", "build-dependencies"):
            for name, spec in (_toml(text).get(section) or {}).items():
                if spec == "*" or (isinstance(spec, dict) and spec.get("version") == "*"):
                    found.append(f"{name}=*")
    return found


def registry_note(filename: str, text: str) -> str | None:
    names = declared_names(filename, text)[:MAX_REGISTRY_LOOKUPS]
    if not names:
        return None

    def look(item: Name) -> list[str]:
        return registry_issues(item[0], item[1], fetch_registry(registry_url(*item)))

    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            issues = [issue for result in pool.map(look, names) for issue in result]
    except (OSError, ValueError) as error:
        return (f"all-you-need registry check on {filename} did NOT run ({type(error).__name__}). Package names are "
                "unverified: confirm each exists before relying on it.")
    if not issues:
        return f"all-you-need registry check on {filename}: all {len(names)} declared packages exist, none new or copyleft-licensed."
    return f"all-you-need registry check on {filename}:\n- " + "\n- ".join(issues)


def report(deps: list[Dep], advisories: list[list[str]], filename: str, truncated: bool = False) -> str:
    scope = f"first {len(deps)} dependencies only (file has more)" if truncated else f"{len(deps)} dependency versions"
    vulnerable = [(d, ids) for d, ids in zip(deps, advisories) if ids]
    if not vulnerable:
        return (f"all-you-need CVE check on {filename}: no known advisories in OSV for {scope}. "
                "Versions given as ranges were checked at their lowest declared version.")
    lines = [f"all-you-need CVE check on {filename}: {len(vulnerable)} of {len(deps)} dependencies have known advisories (OSV), {scope}:"]
    for (_, name, version), ids in vulnerable:
        shown = ", ".join(ids[:MAX_IDS_SHOWN]) + (f" and {len(ids) - MAX_IDS_SHOWN} more" if len(ids) > MAX_IDS_SHOWN else "")
        lines.append(f"- {name} {version}: {shown} (details: https://osv.dev/vulnerability/<id>)")
    lines.append("Pick a patched version from the advisory before keeping these, or tell the user why you are not.")
    return "\n".join(lines)


def check(path: str) -> str | None:
    name = Path(path).name
    parser = PARSERS.get(name.lower())
    if parser is None:
        return None
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    notes = []
    deps = list(dict.fromkeys(parser(text)))                               
    if deps:
        truncated = len(deps) > MAX_DEPS
        deps = deps[:MAX_DEPS]
        try:
            notes.append(report(deps, query_osv(deps), name, truncated))
        except (OSError, ValueError, KeyError) as error:
            notes.append(f"all-you-need CVE check on {name} did NOT run ({type(error).__name__}). Treat these "
                         "dependency versions as unchecked and say so in your reply. Retry when the network is available.")
    if name.lower() in MANIFESTS:
        notes.append(registry_note(name, text))
        loose = unpinned(name, text)
        if loose:
            notes.append(f"all-you-need pin check on {name}: unpinned dependencies ({', '.join(loose[:12])}). Pin exact or narrowly bounded versions and commit the lockfile.")
    return "\n\n".join(n for n in notes if n) or None


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
    note = check((event.get("tool_input") or {}).get("file_path", ""))
    if note:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": note}}))


if __name__ == "__main__":
    main()
