---
name: minimal-diff
description: Solve the whole problem with the least new code. Use on every code change, and when the user mentions over-engineering, bloat, YAGNI or the simplest solution.
---

# minimal-diff

The best code is the code never written. Be lazy about the solution, never about completeness.

## Pick the first option that fully works
1. Does it need to exist? Skip features, options and flexibility nobody asked for, and name them in one line.
2. Already in this codebase (helper, component, pattern)? Use it the way surrounding code does.
3. Standard library or platform feature? Use it, unless the project has its own.
4. Installed dependency? Use it. Never add a dependency for a few lines.
5. One line a reader understands at a glance? Use it. A one-liner that needs decoding is not short.
6. Otherwise write the minimum code that works.

## Rules
- Finish everything the task needs: callers, tests and fixtures the change breaks are part of the change.
- No wrapper, abstraction, option, config, flag, shim or "for later" code nobody asked for. Change internal callers directly instead of adding a compatibility layer.
- Search for an existing equivalent (helper, component, type, constant, test fixture) before writing a new one. Reuse it; extend it only if the change is small and clearly belongs there.
- Do not reformat, reorder imports in, rename in, or restyle code you were not asked to change. Run the formatter only on the lines you touched, or on files that were already formatted.
- Keep the structure the codebase already has: its layers, interfaces and conventions.
- Code you move or merge keeps its error handling and validation.
- Between options of equal size, take the one that is correct on edge cases.
- New non-trivial logic (a branch, loop, parser, money or security path) leaves one small test or assert-based check.
- A shortcut with a known limit goes in the report (the limit and when to upgrade), not in a source comment.

## Never cut
Validation at trust boundaries, error handling that prevents data loss, security, accessibility, anything the user asked for.
