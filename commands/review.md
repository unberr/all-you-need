---
description: Review the current diff for correctness, security and test gaps, with evidence for every finding.
---

# /review

Review the working-tree diff, not the whole repository.

1. Run `git status --short` and `git diff --stat`, then `git diff` (and `git diff --staged` if anything is staged). If this is not a git repository, ask which files changed.
2. Read each changed file in full, plus its callers and the tests that cover it.
3. Report one line per finding: `path:line: severity: problem. Evidence. Suggested fix.`
4. Order by severity: correctness, security, data loss, concurrency, then maintainability.
5. Check the diff for unrequested changes, dead code, debug output, skipped tests, weakened assertions and a half-finished migration.
6. End with either `No findings.` or the shortest list of fixes required before merge.

Do not edit files during this command unless the user asked for fixes. An assessment is the deliverable.
