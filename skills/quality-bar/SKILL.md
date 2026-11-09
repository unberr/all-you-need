---
name: quality-bar
description: The 59-point quality bar for AI-written code plus the security and engineering lists, each mapped to the skill, rule or hook that covers it, with honest status. Use to audit the harness, check work against the full bar, or explain what is guaranteed.
---

# quality-bar

Every point below is mapped to a skill, rule or hook in `references/coverage.md`, with an honest status: enforced by a hook, guided by a skill, partial, or outside what a plugin can control.

## The bar in one screen

**Correctness and reliability:** does exactly what was asked, including edge cases; no invented APIs, parameters, versions or config keys; current idiomatic syntax for the version in use; correct types with no `any`-style escapes; errors handled, never swallowed; complete code with no TODOs, pseudo-code or missing imports; stable behavior; no contradiction with earlier constraints; debugs itself from traces and test failures; admits uncertainty and asks targeted questions; never claims code was tested or built when it was not.

**Code quality:** no slop (filler comments, dead code, repetition, redundant wrappers); readable and self-documenting; idiomatic; simplest thing that works; maintainable; reusable without forced abstraction; refactors that keep behavior.

**Architecture:** separation of concerns; patterns sized to the problem; ready to scale without a rewrite; explained trade-offs.

**Context awareness:** reads the repository before writing; follows its conventions; reuses existing code; knows installed versions; avoids new dependencies; fits the runtime environment; lets the developer inspect the context it used; considers downstream impact.

**Problem solving:** understands the real problem; handles edge cases; prevents bugs; finds root causes; reads errors fully.

**Security:** secure by default against injection, XSS, CSRF, SSRF, unsafe deserialization, path traversal and weak crypto; no hardcoded secrets.

**Performance:** efficient algorithms and data structures; no N+1 queries; safe concurrency; released resources; sound memory handling; lean network payloads; works across operating systems and containers.

**Testing:** meaningful tests that can fail; self-review before replying; runs type checks, linters, formatters and scanners.

**Communication:** follows instructions exactly; minimal surgical diffs; concise explanations; asks only when needed; pushes back when warranted; no sycophancy; clean docs; transparent, with destructive actions explicit and reversible.

**Workflow:** handles large context and long sessions; acts autonomously within scope; responsive.

A second matrix, `references/security-and-engineering-coverage.md`, maps the 30-point security list, the secure-coding and AI guardrail lists, the secure-design list, the 55-point engineering list and the 178-point full-stack list.

## How to use this skill
- Auditing a change: walk the groups above against the diff and the tool output, and report each gap with evidence.
- Auditing the harness: open `references/coverage.md` and check that each row's path still exists and does what it claims. The test suite does the path check.
- Never describe a Guided or Partial point as guaranteed. Say which part is enforced and which depends on the model.
