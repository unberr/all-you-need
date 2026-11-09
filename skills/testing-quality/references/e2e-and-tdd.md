# TDD loop and end-to-end tests

## Red, green, refactor
1. **Red:** write one small test for the next behavior from the acceptance criteria. Run it and watch it fail for the right reason (the assertion, not an import error).
2. **Green:** write the least code that makes it pass. Run the test. Do not add behavior no test asks for.
3. **Refactor:** with tests green, remove duplication and improve names. Run the tests again after each change.
4. Repeat. Commit points are the user's call. At the end run the whole suite, the type checker and the linter.
When there is no test framework, set up the standard one for the language and ecosystem rather than inventing a harness. Delete temporary files and scratch tests you created.

## End-to-end tests (browser)
- Cover only the critical user journeys: sign up and sign in, the money path, the main create-read-update flow. Everything else belongs lower in the pyramid.
- Use a real browser tool (Playwright preferred) against a running test environment with seeded, isolated data. Each test creates and cleans up its own data and does not depend on order.
- Select elements by role, label and visible text, or a dedicated `data-testid`; never by brittle CSS chains. Use a page-object or helper layer for repeated flows.
- Wait for conditions, never fixed sleeps: auto-waiting locators, `expect` with retries, network idle only where it is truly the signal.
- Capture a trace, screenshot and video on failure so a CI failure can be diagnosed. Run in CI on every pull request for the critical set.
- Flaky tests: find the race (missing wait, shared data, time dependence) and fix it. Quarantine only with an owner and a ticket; never loop retries to hide it.
- Include accessibility checks (axe) on key pages, and run at least one mobile viewport.
