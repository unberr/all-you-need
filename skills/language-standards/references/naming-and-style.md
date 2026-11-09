# Naming and style defaults

Defaults, written down so you do not invent answers. The project's established convention beats this file, and the user's instruction beats both, immediately and for the rest of the conversation.

## Naming in three layers
1. **The language decides identifier casing.** Follow its formatter and standard library: snake_case functions and variables in Python and Rust, mixedCaps in Go, camelCase values in JavaScript and TypeScript, PascalCase methods in C#. Types are PascalCase wherever available, with no Hungarian prefixes and no `Impl` suffixes unless the language convention calls for them (`IFoo` is right in C#, wrong in TypeScript).
2. **Anything that leaves the language uses snake_case:** database tables, columns, indexes and constraints; environment variables in SCREAMING_SNAKE; configuration keys; cache keys. Two universal exceptions: command-line flags are kebab-case, HTTP headers are Kebab-Titled.
3. **Wire payload field casing is a project-wide decision.** Pick snake_case or camelCase for the whole interface and convert at exactly one place. Two conversion points means two sources of truth.

## Files and directories
- kebab-case wherever the language permits: TypeScript, JavaScript, CSS, HTML, Markdown, shell scripts, configuration, SQL migrations, assets, and every directory in those trees.
- The language wins where it ties names to imports or types: snake_case modules in Python and Rust, lowercase with `_test.go` in Go, the type's own name in Java, Kotlin and C#. Never mix two file conventions in one directory.
- Files hold one job; split early. Organize by what code is for, not by kind of file. No `utils`, `helpers`, `common` or `misc` files: shared logic with two or more real callers gets a module named for what it does.
- Every module is one of three things: an entry point, a boundary that talks to something outside the process, or internal. Validation belongs in boundary modules; a module that cannot say which it is probably has two jobs.
- Never hand-edit a generated file. Regenerate it, or change the generator.

## Names
- Descriptive and pronounceable, four characters or more. No single letters and no abbreviations that cost a lookup, except where short is clearer: `id`, `db`, `url`, `io`, `ok`, and a loop index in a short loop.
- Booleans read as assertions: `is`, `has`, `should`, `can`. A function that does something is verb-first; one that returns a value is named for the value. One word beats two when unambiguous.

## Style
- Immutable bindings by default; a conditional expression instead of a mutable binding assigned later.
- Early returns, and never an `else` after a return.
- Do not rely on implicit truthiness where it matters: distinguish absent, empty and zero explicitly.
- Never escape the type system: no `any`, unchecked cast, `interface{}` standing in for a real type, `Object`, `dynamic`, `# type: ignore`, `unsafe` block or leftover suppression comment. If you cannot express the type, the design is wrong, not the checker.
- Errors surface; see the `error-handling` skill.
- Logs are greppable: one consistent prefix or logger per service, never a secret, token or personal data in a log line, error message or fixture.
- Plain output: no emoji in code, commit messages, file names, logs or terminal output; no decorative unicode (box drawing, arrows, typographic dashes) in source. ASCII unless the content genuinely needs otherwise.
- Comments: write none by default; carry intent in names, named intermediate values, smaller functions and explicit types. Never write a comment that describes the next line, explains your change to a reviewer, banners a block, restates a function name, holds a TODO you are not resolving, keeps a commented-out alternative, or narrates your process. Where the project or the user requires comments (public API docstrings, license headers), add exactly what is required. Match the file's idiom, not its comment density, and never delete or shorten existing comments you were not asked to change.
