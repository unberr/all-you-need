---
name: testing-quality
description: Write meaningful tests: unit, integration, edge-case and regression tests that fail when the code is wrong. Use whenever adding or changing tests, or when asked to test code, raise coverage, or check that existing tests are worth anything.
paths:
  - "**/test/**"
  - "**/tests/**"
  - "**/__tests__/**"
  - "**/*.test.*"
  - "**/*.spec.*"
---

# testing-quality

A test is useful only if it can fail for the right reason. A test written to pass proves nothing.

## What to test
- Behavior through the public interface: inputs in, outputs and side effects out. Not private helpers, not call order, not framework internals.
- For each unit: the normal case, and the edges. Empty, one, many, maximum, boundary values (0, -1, off-by-one), invalid input, null or missing, duplicate, unicode and very long text, timezone and daylight-saving boundaries, concurrent calls, partial failure (network down, disk full, timeout), permission denied.
- Every bug fix gets a regression test written first, shown failing, then passing.
- Integration tests cross one real boundary (database, HTTP server, file system) with test data they create and clean up. A few end-to-end tests cover the critical user paths.

## Kinds of tests and when to write each
- **Unit:** pure logic, parsers, calculations, validators.
- **Integration:** across one real boundary (database, queue, HTTP server).
- **End-to-end:** the few critical user workflows across the whole stack.
- **Regression:** one per fixed bug, written first.
- **Edge-case:** the list above, per unit.
- **Security and authorization:** access control, IDOR, injection, malformed input, expired tokens, abuse of business logic. Write them from the requirement and make sure each fails when the control is removed. See `secure-code` (`references/security-testing.md`).
- **Concurrency:** simultaneous requests and competing writes against the same row or resource; run with a race detector where the language has one.
- **Failure:** database down, timeouts, unavailable dependency, malformed upstream response, disk full, partial writes; assert the system degrades safely and reports honestly.
- **Performance:** a realistic-load check or benchmark for the hot path, with numbers, when the change touches it.
- **Reproducible:** a failure must be deterministic and easy to investigate: fixed seeds, fake clocks, isolated data.

## Make each test honest
- One reason to fail per test; a name that states the behavior ("rejects expired tokens"). Arrange, act, assert, in that order, with real assertions on the result that matters.
- Never: `assert True`, `expect(true).toBe(true)`, an assertion that compares a value to itself, a test with no assertion, a test that only checks "does not throw" when a value is the point, or an assertion on a mock you just configured.
- Do not skip, `xit`, `@Ignore` or comment out a failing test to go green. Fix the code or the test, or report it.
- Mock only what you must (network, clock, randomness, slow or paid services). Do not mock the unit under test or its collaborators in the same module; that tests the mock.
- Tests are deterministic: fixed seeds, fake clocks, no dependence on test order, wall time, the network, the machine's locale or leftover files. Each test creates its own data.
- Parameterize instead of copy-pasting similar tests. Use property-based tests (hypothesis, fast-check, proptest, QuickCheck-style) for parsers, serializers, math and invariants.

## Prove the test can fail (mutation check)
After a test passes, break the code on purpose (flip a condition, remove a line, return a constant) and confirm the test fails. If it still passes, the test is not checking that behavior. Restore the code. Use a mutation tool (mutmut, Stryker, cargo-mutants) when the project has one.

## Coverage
Line coverage is a floor, not a goal. Read what is uncovered: error paths and branches matter more than getters. Never write tests only to move a percentage.

## Run and report
Run the full suite, read the output, and report counts and failures as they are. Say which kinds of tests you did not write and why (for example, no database available).
