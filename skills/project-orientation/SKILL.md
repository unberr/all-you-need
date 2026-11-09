---
name: project-orientation
description: Orient before working: toolchain from the project's own files, lockfile and runtime pins, monorepo layout, instruction files, generated files, what to persist across compaction. Use at the start of any code-editing task or when tooling sources disagree.
---

# project-orientation

You cannot write correct code for a project you have not looked at. Orientation is the first part of the work. A session hook already detects many facts and injects them as "Project facts"; treat that list as a starting point and confirm what matters.

## Three things that are absolute
1. Do not edit a file you have not read.
2. Do not add a feature to a project you have not oriented in.
3. Do not invent a command when the project declares one.

## Proportional depth
- **Question about code:** read the code the question is about.
- **Edit to an existing file:** read that file, and know the project's declared build and test commands.
- **New feature, structural change, or more than one file:** the full survey below.
- **A typo in a string:** no survey. A rule that makes every trivial task cost ten tool calls gets ignored.

## The survey
1. **Platform.** Operating system, shell, path separators and line endings that matter for what you will write. A command valid in one shell can be a parse error in another.
2. **Toolchain from the project's own files, not from convention and not from what is installed.** The lockfile decides the package manager: `bun.lockb`/`bun.lock` is bun, `pnpm-lock.yaml` pnpm, `package-lock.json` npm, `yarn.lock` yarn; `uv.lock`, `poetry.lock`, `Pipfile.lock` or a bare `requirements.txt` for Python; `Cargo.lock`; `go.sum`; `Gemfile.lock`; `composer.lock`; a committed `mvnw` or `gradlew` wrapper over a system binary. Runtime versions come from `.nvmrc`, `.node-version`, `.tool-versions`, `engines`, `requires-python`, the `go` directive, `rust-toolchain.toml`, `global.json`.
3. **Declared commands.** `package.json` scripts, Makefile targets, `pyproject.toml` tool sections, CI configuration. Use those exact commands for build, test, lint, type check and format.
4. **Layout.** Where source, tests and configuration live; the entry points; which files are generated (never hand-edit them: regenerate, or change the generator). In a monorepo, find workspace markers (`pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, `workspaces`, a Cargo workspace, `go.work`), establish which package you are in, and run commands from that package unless the tooling says otherwise.
5. **Project instructions.** `CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.agents/`, a contributing guide, and every file they include. A harness may inject some of them, not necessarily all. When two disagree, the one nearest the file you are working on wins.
6. **Packaged guidance.** If skills or bundled instructions cover the kind of work, read them before producing; they often encode installed libraries and renderer limits you cannot derive.

## When the sources disagree, do not resolve it quietly
Two lockfiles, a `packageManager` field that contradicts the lockfile, a README that documents a command the manifest does not define, or CI scripts that differ from the manifest: check which is current and what CI uses. If it is genuinely ambiguous, ask the user. This is a legitimate blocking question: it is information only they have, and the wrong toolchain wastes the whole turn.

## Persist what you found
Do the survey once. Record the package manager, runtime, build and test commands, workspace layout and generated files in the task ledger or a lesson, so a context compaction does not force a re-derivation. After a compaction, treat any summary as incomplete: its silence is not evidence something did not happen. Re-read any file you read before the boundary before editing it.

## Before you edit
Re-read the file if it may have changed (the user edited it, a formatter or watcher rewrote it, a build regenerated it, another agent touched it). An edit that fails to match is evidence the file changed: find out what changed before retrying with a looser match. If the file no longer looks like what you read, stop and report.
