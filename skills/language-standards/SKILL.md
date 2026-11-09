---
name: language-standards
description: Per-language standards for fullstack work in Python, JavaScript, TypeScript, C, C++, Rust, C#, Go, PHP, HTML and CSS: the toolchain commands to run, idioms, security pitfalls and testing habits. Use whenever writing, fixing or reviewing code in one of these languages.
paths:
  - "**/*.py"
  - "**/*.pyi"
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.mjs"
  - "**/*.cjs"
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.c"
  - "**/*.h"
  - "**/*.cc"
  - "**/*.cpp"
  - "**/*.hpp"
  - "**/*.rs"
  - "**/*.go"
  - "**/*.cs"
  - "**/*.php"
  - "**/*.html"
  - "**/*.css"
---

# language-standards

Load only the reference for the language you are working in. Each reference lists the check commands, the idioms that prevent the common defects, and the security pitfalls.

| Working in | Read |
| --- | --- |
| Python | `references/python.md` |
| JavaScript, Node.js, React | `references/javascript.md` |
| TypeScript | `references/typescript.md` (also read `javascript.md`) |
| C | `references/c.md` |
| C++ | `references/cpp.md` |
| Rust | `references/rust.md` |
| C# and .NET | `references/csharp.md` |
| Go | `references/go.md` |
| PHP | `references/php.md` |
| HTML and CSS | `references/html-css.md` (design: skill `ui-craft`) |

## Rules that hold in every language
1. The project's own declared commands and configuration beat these references. Read `package.json` scripts, `pyproject.toml`, `Makefile`, `Cargo.toml`, `go.mod`, `*.csproj`, `composer.json` first, and use their versions of the formatter, linter and test runner.
2. Run the formatter, the linter, the type checker or compiler with warnings on, and the tests. Read the output. A language's own checks catch more than review does.
3. Validate at boundaries (user input, files, network, environment), trust the inside. Parse into typed values at the edge.
4. Handle errors where you can act on them. Never swallow one; never expose internals to the user.
5. Use parameterized queries, argument-list process calls and context-aware output encoding. Never build SQL, shell commands or HTML by joining strings with input.
6. Secrets come from the environment or a secret store, never from source, fixtures, logs or URLs.
7. Check dependency versions against known advisories (see `secure-code`) and pin them with a lockfile.
8. Money uses a decimal or integer minor-unit type, never binary floating point. Time uses timezone-aware values, stored in UTC.
9. Every network call has a timeout. Every resource that opens is closed on every path. Concurrency has a clear owner for each piece of shared state.
10. Tests cover behavior and edge cases (empty, one, many, invalid, boundary), run without network access, and do not depend on each other's order.
