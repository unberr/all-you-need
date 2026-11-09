# Coverage of the 59-point quality bar

Status meanings: **Enforced** = a hook checks it mechanically on every relevant edit or turn. The stop gate and the guards block; the lint and CVE hooks only report findings to the model and never block, so for them Enforced means detected, not guaranteed. **Guided** = a skill or rule instructs it; compliance depends on the model. **Partial** = some of it is enforced or guided, the rest is outside the plugin. **Outside** = not controllable from a plugin.

A test (`tests/test_coverage.py`) fails if a row is missing or if a path named here does not exist.

| # | Requirement | Where | Status | How |
| --- | --- | --- | --- | --- |
| 1 | Functional correctness incl. edge cases | `skills/all-you-need`, `skills/testing-quality`, `skills/all-you-need/references/rigor.md` | Guided | Acceptance criteria and edge-case list before coding; tests that must be able to fail; falsification pass. Correctness itself depends on the model. |
| 2 | No hallucinated APIs | `skills/all-you-need`, `hooks/core-rules.md`, `install.sh` | Partial | Rule: never use a symbol not seen in installed code, docs for the version, or the language server. Language-server plugins and the check gate make invented names fail loudly. Not preventable, only caught. |
| 3 | Current language, framework and version knowledge | `skills/all-you-need`, `skills/language-standards`, `hooks/cve_check.py` | Guided | Read lockfile, installed source or current docs; check deprecations. Per-language references name version-dependent facts. |
| 4 | Correct types and interfaces, no escape hatches | `skills/language-standards`, `skills/clean-code`, `hooks/slop_lint.py` | Enforced | Lint flags any, ts-ignore, type-ignore; strict-mode rules per language; language servers report type errors. |
| 5 | Proper error handling | `skills/clean-code`, `hooks/slop_lint.py` | Enforced | Lint flags empty catch, bare except, except-pass, swallowed errors in Python, TypeScript, C#; guided elsewhere. |
| 6 | Complete implementations, no TODOs or placeholders | `hooks/slop_lint.py`, `hooks/stop_gate.py`, `skills/finish-the-job` | Enforced | Lint flags TODO, stubs and placeholder comments; the check gate fails on missing imports through compile and type checks; ledger blocks dropping parts. |
| 7 | Deterministic, reproducible behavior | `skills/testing-quality`, `skills/performance-reliability`, `hooks/hooks.json` | Partial | Harness side only: pinned versions and lockfiles, seeded tests, fixed clocks, deterministic hooks. Sampling determinism of the model is set by the API and is not controllable from a plugin. |
| 8 | Self-consistency and remembering constraints | `skills/finish-the-job`, `skills/all-you-need`, `hooks/session_start.py` | Guided | A Constraints line in the ledger is re-read before finishing; core rules and the ledger are re-injected after compaction. |
| 9 | Self-correction loop | `skills/debugging`, `hooks/stop_gate.py` | Guided | Loop on each new trace or failing test; stop and re-hypothesize after two failures. The check gate blocks finishing after an edit without a passing check. |
| 10 | Admits uncertainty, states assumptions, asks targeted questions | `skills/all-you-need`, `skills/all-you-need/references/rigor.md`, `skills/secure-code` | Guided | Verified, believed, unknown labels; confidence levels; one targeted question only when the answer changes the outcome. |
| 11 | No false claims of success | `hooks/stop_gate.py`, `hooks/slop_lint.py` | Enforced | Honesty gate requires a Not verified line after code edits; check gate requires an exit-0 check after the last edit; lint flags stubs and tests that cannot fail. |
| 12 | No slop | `skills/clean-code`, `skills/minimal-diff`, `hooks/slop_lint.py` | Partial | Lint catches TODOs, placeholders, emoji, rigged tests; the rest (filler comments, wrappers, repetition) is guidance and review. |
| 13 | Readable and self-documenting | `skills/clean-code`, `skills/code-structure` | Guided | Naming, early returns, no clever one-liners, size guidance. |
| 14 | Idiomatic code | `skills/language-standards` | Guided | One reference per language with idioms and anti-patterns. |
| 15 | Appropriate simplicity, minimal abstraction | `skills/minimal-diff`, `skills/code-structure` | Guided | First-option-that-works ladder; patterns only when the problem has their shape. |
| 16 | Maintainability | `skills/clean-code`, `skills/code-structure`, `skills/refactoring` | Guided | Structure, naming, tests, docs, small functions. |
| 17 | Reusability without forced abstraction | `skills/clean-code`, `skills/minimal-diff` | Guided | Extract on the third repetition; reuse existing code first. |
| 18 | Clean refactoring without behavior change | `skills/refactoring` | Guided | Characterization tests first, small verified steps, contracts untouched. |
| 19 | Good structure and separation of concerns | `skills/code-structure` | Guided | Layers, dependency direction, module boundaries, size guidance. |
| 20 | Patterns scaled to the problem | `skills/code-structure`, `skills/minimal-diff` | Guided | Patterns section; no interface for one implementation. |
| 21 | Scalability readiness | `skills/performance-reliability`, `skills/code-structure` | Guided | Stateless services, pagination, indexes, queues, external config, no pre-built distribution. |
| 22 | Technical judgment and trade-offs | `skills/all-you-need`, `skills/code-structure` | Guided | State the trade-off in a sentence when choosing between options; push back on bad approaches. |
| 23 | Repository-wide understanding | `skills/all-you-need`, `agents/reviewer.md` | Guided | Orient step: read callers, tests, conventions before writing; reviewer reads whole files, not only the diff. |
| 24 | Follows existing conventions | `skills/all-you-need`, `skills/minimal-diff` | Guided | Note style, lint config, naming, test framework; match them; no reformatting of untouched code. |
| 25 | Reuses existing code before duplicating | `skills/all-you-need`, `skills/minimal-diff` | Guided | Search for an existing equivalent first. |
| 26 | Dependency and version awareness | `skills/all-you-need`, `hooks/cve_check.py` | Partial | Read lockfile and installed versions; manifests and lockfiles are checked against OSV on edit. |
| 27 | No unnecessary dependencies | `skills/minimal-diff`, `templates/settings.json` | Guided | Standard library and installed packages first; a new dependency needs a stated reason. The settings template makes package installs ask first. |
| 28 | Runtime environment awareness | `skills/all-you-need`, `skills/performance-reliability` | Guided | Orient step lists OS, runtime, database, framework and deployment target; cross-platform and container rules. |
| 29 | Context control and transparency | `skills/all-you-need`, `skills/finish-the-job`, `hooks/session_start.py` | Partial | Reports which files were read and what was assumed; the ledger is a visible, editable file. Which context the host loads is controlled by the host application. |
| 30 | Does not break things | `skills/all-you-need`, `skills/refactoring`, `agents/reviewer.md` | Guided | Blast-radius list, caller search, reviewer checks missed callers. |
| 31 | Deep reasoning about the real problem | `skills/all-you-need`, `skills/debugging`, `skills/all-you-need/references/rigor.md` | Guided | Frame step restates goal and criteria before code. |
| 32 | Edge-case handling | `skills/testing-quality`, `skills/all-you-need/references/rigor.md`, `skills/language-standards` | Guided | Explicit edge-case checklist for tests and for the break-it pass. |
| 33 | Bug prevention | `skills/all-you-need/references/rigor.md`, `skills/language-standards`, `hooks/slop_lint.py` | Partial | Falsification pass, language-specific pitfalls, lint for known bug patterns such as mutable defaults and unsafe blocks. |
| 34 | Root-cause analysis | `skills/debugging` | Guided | Reproduce, rank hypotheses, fix at the root, no blind retries or sleeps. |
| 35 | Reads errors carefully | `skills/debugging` | Guided | Read the whole trace and the cause chain; first compiler error first. |
| 36 | Secure by default | `skills/secure-code`, `hooks/slop_lint.py`, `hooks/cve_check.py` | Enforced | Pattern table (injection, XSS, CSRF, SSRF, deserialization, path traversal, crypto); lint for common holes; OSV lookups. Lint is pattern-based, not complete. |
| 37 | No hardcoded secrets | `hooks/slop_lint.py`, `templates/settings.json`, `skills/secure-code` | Enforced | Lint flags secret-like assignments; settings template denies reading secret files; rule to use environment config. |
| 38 | Performance awareness | `skills/performance-reliability` | Guided | Measure first; avoid obvious waste; profile hot paths. |
| 39 | Efficient algorithms and data structures | `skills/performance-reliability` | Guided | Complexity statement, set and map lookups, avoid accidental quadratic work. |
| 40 | Database and ORM efficiency | `skills/performance-reliability` | Guided | N+1, indexes, pagination, transactions, safe migrations. |
| 41 | Concurrency safety | `skills/performance-reliability`, `skills/language-standards` | Guided | Shared-state ownership, lock ordering, async rules, race detectors. |
| 42 | Resource safety | `skills/performance-reliability`, `skills/language-standards` | Guided | Release on every path; bounded queues and caches. |
| 43 | Memory management | `skills/performance-reliability`, `skills/language-standards`, `hooks/slop_lint.py` | Partial | Ownership rules, sanitizers and Miri; lint flags unbounded C string calls and unsafe without a SAFETY comment. |
| 44 | Network and payload efficiency | `skills/performance-reliability`, `skills/ui-craft/references/web-frontend.md` | Guided | Batching, compression, conditional requests, timeouts with backoff, less JavaScript. |
| 45 | Cross-platform compatibility | `skills/performance-reliability`, `install.sh`, `hooks/hooks.json` | Partial | Rules for paths, encodings, containers; installer and hooks handle macOS, Linux and Windows (Linux and Windows paths were tested by simulation only). |
| 46 | Meaningful tests | `skills/testing-quality`, `hooks/slop_lint.py` | Enforced | Lint flags tests that cannot fail and skipped tests; mutation check and edge-case rules in the skill. |
| 47 | Self-review before responding | `skills/all-you-need`, `skills/all-you-need/references/rigor.md` | Guided | A trace-through checklist: imports, types, criteria, error paths, resources, secrets, diff scope. |
| 48 | Tool use and validation | `hooks/stop_gate.py`, `install.sh`, `skills/all-you-need` | Enforced | Check gate recognizes build, test, lint, type check and scanner commands; companion plugins add language servers and static analysis. |
| 49 | Follows instructions precisely | `skills/all-you-need` | Guided | Frame step: exact language, framework, version and format; constraints list re-read at the end. |
| 50 | Minimal, surgical diffs | `skills/minimal-diff`, `agents/reviewer.md` | Guided | Every changed line traces to the request; no mass reformatting; reviewer flags unrelated changes. |
| 51 | Concise, useful explanations | `skills/all-you-need/references/terse-voice.md` | Guided | Answer first; why only when it helps. |
| 52 | Smart clarification | `skills/all-you-need` | Guided | Ask one targeted question only when the answer changes the outcome. |
| 53 | Pushes back when warranted | `skills/all-you-need`, `skills/all-you-need/references/terse-voice.md` | Guided | Flag a bad approach or a bug in the request with reason and alternative before building. |
| 54 | No sycophancy | `skills/all-you-need/references/terse-voice.md` | Guided | Peer tone rules: no praise, no flattery, no apology loops. |
| 55 | Clean documentation | `skills/clean-code` | Guided | Docstrings, README and API doc guidance. |
| 56 | Transparency and control | `skills/all-you-need`, `templates/settings.json`, `hooks/core-rules.md` | Partial | Confirm destructive and outward actions, prefer reversible options, flag generated code, do not send code externally unasked; settings template denies destructive commands. |
| 57 | Handles large context | `skills/finish-the-job`, `hooks/session_start.py`, `hooks/stop_gate.py` | Partial | Ledger survives compaction and blocks premature stopping. It does not enlarge the context window. |
| 58 | Agentic competence within scope | `skills/all-you-need`, `hooks/stop_gate.py`, `templates/settings.json` | Partial | Runs checks, loops on failures, stays in scope, asks before destructive actions; permissions are enforced by the host settings. |
| 59 | Real-time responsiveness | `hooks/hooks.json` | Outside | Inline-completion latency belongs to the editor and the model service. The plugin only keeps its hooks fast (local Python, network only on dependency-file edits). |
