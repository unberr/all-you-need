---
description: Run the six-phase verification loop and report PASS, FAIL or PARTIAL with the exact commands.
---

# /verify

Load the `verification-loop` skill and run it against the current working tree.

1. Read the project's manifests, CI configuration and instruction files to find the declared build, type-check, lint and test commands. Do not invent commands.
2. Run each phase in order: build, type check, lint, tests, dependency and secret scan, diff review.
3. Stop at the first hard failure. Fix only failures caused by the current change; report pre-existing failures separately with evidence.
4. Rerun any phase whose inputs changed after the last edit.
5. End with the report block from the skill: one line per phase, the command, the exit code and the meaningful output. Mark unconfigured phases `NOT RUN`, never `PASS`.

Do not delete, skip or weaken a test to reach green. Do not auto-fix formatting during verification unless the project's check does that itself.
