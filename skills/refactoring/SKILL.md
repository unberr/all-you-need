---
name: refactoring
description: Safely improve messy or legacy code without changing its external behavior or breaking contracts. Use when asked to refactor, clean up, modernize, simplify, rename, split or migrate code.
---

# refactoring

Refactoring means changing structure while behavior stays identical. If behavior changes, it is not a refactor: say so and do it as a separate change.

## Before touching anything
1. Pin the behavior. Find the existing tests for the code. If coverage is thin, write characterization tests first: call the code with real inputs, record what it actually returns (including odd results and errors), and assert exactly that. Run them green on the untouched code.
2. Map the contract: public functions, exported names, HTTP routes, CLI flags, file formats, database schema, events, logs others parse. Find every caller (search by name, import, string reference, reflection, config, docs, other repositories if known). These do not change unless the user asked.
3. State the goal in one line ("split this 900-line module", "replace callback style with async"). Anything outside it is out of scope.

## Do it in small, verified steps
- One kind of change per step: rename, extract function, move file, inline, replace a pattern. Run the tests after each step. A red test means undo that step, not patch forward.
- Prefer the editor or language-server refactoring (rename symbol, extract) over find-and-replace; it follows references.
- Add the new form, move callers to it, then remove the old form. Never leave the tree half migrated at the end of a step.
- Keep commits or change sets reviewable: formatting-only changes are separate from logic moves.
- Do not mix in bug fixes. A bug found on the way is noted and reported, or fixed separately with its own test, unless the user says otherwise.

## What good looks like
- Smaller functions with one job, names from the domain, no dead code, no duplicated blocks (extract on the third repetition, not the second), fewer parameters and flags, clearer error handling, the same public behavior.
- Delete only code your refactor orphaned. Report other dead code you noticed; do not remove it unasked.

## Done when
The pre-existing tests and the characterization tests pass unchanged, type checks and linters are clean, public contracts are untouched (say how you checked), and the diff contains only the refactor. Report any behavior you chose to preserve even though it looks wrong.
