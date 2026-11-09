---
name: verification-loop
description: A six-phase verification pass with a PASS/FAIL report: build, type check, lint, tests, dependency and secret scan, diff review. Use after a feature, before a pull request, before declaring done, or when a check must be proved rather than assumed.
---

# verification-loop

Verification is a sequence, not a feeling. Run the phases in order, stop at the first hard failure, and report exactly what ran.

## Phase 0: declare the commands
Read the project's manifests and CI before running anything: `package.json` scripts, `Makefile`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `composer.json`, `.github/workflows`, and the instruction files. Use the declared command. If none exists, say so and name the closest equivalent you ran.

Record the command, the working directory and the exit code for every phase. A phase with no configured command is `NOT RUN`, never `PASS`.

## Phase 1: build or compile
Run the project's build. A build failure stops the loop: fix it before continuing. Do not treat a dev-server start as a build.

## Phase 2: type check
Run the declared type checker in strict mode where the project supports it. Read the first errors first; later ones are often consequences. Report the count and the first few messages, not a wall of output.

## Phase 3: lint and format check
Run the project's linter and formatter check without auto-fix. A formatter that rewrites files during verification changes the diff you are about to review. If the project has no linter, say `NOT RUN` and why.

## Phase 4: tests
Run the full suite, not only the tests you touched. Use the project's runner and configuration. If coverage is configured, report the number the tool printed; do not estimate it. If a test is flaky, rerun it once and report both results; do not delete or skip it. A skipped or `xfail` test is not a pass.

## Phase 5: dependency, secret and unsafe-pattern scan
Check the dependency changes against the project's audit tool or OSV. Search the diff for secrets, credentials, private keys and tokens. Run the repository's security scanner when it has one; here that is `python3 scripts/security_scan.py --root .`. Report findings by severity, not as a total.

## Phase 6: diff review
Read the complete diff before reporting. Check that every changed line traces to the request, that no debug print, scratch file or commented-out code remains, and that callers, tests and docs were updated together. Look for a half-finished migration: a new path added while the old one still runs.

## Report
```
Verification: PASS | FAIL | PARTIAL
Build:        PASS  (pnpm build, exit 0)
Types:        PASS  (tsc --noEmit, exit 0)
Lint:         PASS  (eslint ., exit 0)
Tests:        PASS  (vitest run, 84 passed)
Security:     PASS  (security_scan.py, grade A)
Diff:         PASS  (7 files, all in scope)
Not run:      integration tests (need a live database)
```
- `PASS` means the command exited 0 and you read the result.
- `FAIL` means it exited non-zero. Include the failing command and the first actionable error.
- `PARTIAL` means some phases did not run or a known failure is unrelated to this change. Name which and why.
- Never convert `NOT RUN` into `PASS` because the change is small.

## Rules
- Run the loop after the last edit, not before it.
- Re-run any phase whose inputs changed.
- Do not weaken a check, delete a test, add a suppression or lower a threshold to reach green. Fix the cause or report the failure.
- If the suite takes too long, run the affected subset first, then the full suite before declaring done. State which was run.
- The final report belongs in the reply, not only in a log file.
