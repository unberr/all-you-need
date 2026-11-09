---
name: clean-code
description: Code-quality rules for types, errors, validation, comments, performance, accessibility and network code. Use whenever writing or editing code.
---

# clean-code

## Types and errors
- Never escape the type system: no `any`, unchecked casts, or `type: ignore` to silence a real error.
- Catch the specific failure. Never swallow an error, never use an empty catch or bare except.
- Validate at boundaries only: user input, environment, files, external APIs. Trust internal code.

## Structure
- No single-implementation interface, single-value config, stub, TODO or half-wired path.
- No feature flags or compatibility shims for internal code. Add the new form, migrate callers, remove the old form; the tree stays coherent after each step.
- Comments explain the why the code cannot show, in one line. Do not delete or shorten comments you were not asked to change.
- Never hand-edit generated files.

## Readability and reuse
- Names carry the meaning; a reader should follow the code without the comments. Straight control flow: early returns over deep nesting, no clever one-liners, no boolean parameters that switch behavior.
- Follow the language's and the project's idioms (naming case, error style, standard library first). Do not write one language in the accent of another.
- Extract a shared helper on the third repetition, not the second, and only when the copies change for the same reason. A reusable component takes the parameters it needs today, not options for imagined uses.
- No filler comments that restate the code, no commented-out code, no dead code, no wrapper that only forwards a call.

## Documentation
- Public functions, classes and modules get a short docstring: what it does, parameters, return value, what it raises, and any non-obvious precondition. Do not document the obvious.
- A README covers what the project is, how to install, run and test it, and how to configure it. Update it when behavior or setup changes.
- API docs state every endpoint's inputs, outputs, errors and auth. Keep examples runnable.

## Performance
- Optimize hot paths, I/O, allocations, N+1 queries and algorithmic complexity. Leave cold code readable.

## Network-exposed code
- Say when something has no authentication.
- Parameterized queries, output encoding, secrets from the environment, timeouts and size caps on network calls.

## UI
- Semantic elements, labelled controls, logical focus order, sufficient contrast, announced state. It must work by keyboard and screen reader.

## Hygiene
- No emoji in code, commits or logs. No secrets in logs or fixtures.
- New dependency: say why, pin the version, and check the package name against typosquats. Never pipe a remote script to a shell.
- Before finishing: run build, lint, type-check and tests, read the output, and re-read the diff for anything deletable.
