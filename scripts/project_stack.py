#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

SKIP_DIRS = {".git", ".hg", ".svn", ".venv", "venv", "node_modules", "vendor", "target", "dist", "build",
             "coverage", "__pycache__", ".next", ".nuxt", ".turbo"}
MAX_FILES = 20000
MAX_DEPTH = 7

EXTENSIONS = {
    ".py": "python", ".pyi": "python", ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
    ".cjs": "javascript", ".ts": "typescript", ".tsx": "typescript", ".rs": "rust", ".go": "go",
    ".c": "c_cpp", ".h": "c_cpp", ".cc": "c_cpp", ".cpp": "c_cpp", ".cxx": "c_cpp", ".hpp": "c_cpp",
    ".hh": "c_cpp", ".cs": "csharp", ".php": "php", ".java": "java", ".kt": "kotlin", ".kts": "kotlin",
    ".swift": "swift", ".rb": "ruby", ".scala": "scala", ".html": "web",
    ".css": "web", ".scss": "web", ".vue": "web", ".svelte": "web",
    ".sh": "shell", ".sql": "sql",
}
MARKERS = {
    "pyproject.toml": "python", "requirements.txt": "python", "Pipfile": "python", "Cargo.toml": "rust",
    "go.mod": "go", "composer.json": "php", "package.json": "javascript", "tsconfig.json": "typescript",
    "CMakeLists.txt": "c_cpp", "Cargo.lock": "rust", "pom.xml": "java", "build.gradle": "java",
    "build.gradle.kts": "kotlin", "Package.swift": "swift", "Gemfile": "ruby",
}
LANGUAGE_CONFIG = {
    "python": ("pyright", "pyright-lsp@claude-plugins-official"),
    "javascript": ("typescript-language-server", "typescript-lsp@claude-plugins-official"),
    "typescript": ("typescript-language-server", "typescript-lsp@claude-plugins-official"),
    "rust": ("rust-analyzer", "rust-analyzer-lsp@claude-plugins-official"),
    "go": ("gopls", "gopls-lsp@claude-plugins-official"),
    "c_cpp": ("clangd", "clangd-lsp@claude-plugins-official"),
    "csharp": ("csharp-ls", "csharp-lsp@claude-plugins-official"),
    "php": ("intelephense", "php-lsp@claude-plugins-official"),
}


def detect(root: Path) -> dict[str, list[str] | bool]:
    languages: set[str] = set()
    inspected = 0
    for current, dirs, files in os.walk(root):
        relative = Path(current).relative_to(root)
        if len(relative.parts) >= MAX_DEPTH:
            dirs[:] = []
        else:
            dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith("."))
        for name in files:
            inspected += 1
            if name in MARKERS:
                languages.add(MARKERS[name])
            if name.endswith((".csproj", ".sln")):
                languages.add("csharp")
            language = EXTENSIONS.get(Path(name).suffix.lower())
            if language:
                languages.add(language)
            if inspected >= MAX_FILES:
                break
        if inspected >= MAX_FILES:
            break

    ordered = sorted(languages)
    tools = sorted({LANGUAGE_CONFIG[language][0] for language in languages if language in LANGUAGE_CONFIG})
    companions = sorted({LANGUAGE_CONFIG[language][1] for language in languages if language in LANGUAGE_CONFIG})
    has_source = bool(languages)
    if has_source:
        companions.append("security-guidance@claude-plugins-official")
    return {"languages": ordered, "tools": tools, "companions": sorted(set(companions)), "has_source": has_source}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--field", choices=("languages", "tools", "companions", "setup", "json"), default="json")
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        parser.error(f"project directory does not exist: {root}")
    result = detect(root)
    if args.field == "json":
        print(json.dumps(result, sort_keys=True))
    elif args.field == "setup":
        for field in ("tools", "companions"):
            for value in result[field]:
                print(f"{field}\t{value}")
    else:
        print("\n".join(result[args.field]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
