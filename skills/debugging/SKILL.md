---
name: debugging
description: Root-cause debugging and the self-correction loop: reproduce, read the whole error, form ranked hypotheses, test one, fix at the cause, prove with a regression test. Use for any bug, failing test, build error, stack trace, crash or "it does not work".
---

# debugging

A patch that makes the symptom go away without explaining it is a guess. Find the mechanism first.

## 1. Reproduce
- Get the exact failing command, input and environment. Run it and see the failure yourself before changing anything.
- Cannot reproduce: say so, and list what differs (version, data, OS, config, timing). Do not "fix" what you cannot observe.

## 2. Read the evidence completely
- Read the whole error output, not the first or last line: the exception type, the message, every frame of the stack trace, and the "caused by" chain. The failing frame in your code is usually not the top one.
- Compiler and type errors: fix the first error first, since later ones are often consequences. Quote the exact message when you report it.
- Logs: look at what happened before the failure, not only the failure line. Check timestamps and request ids.
- Test failures: read expected versus actual, then read the test itself. A wrong test is a possible cause.

## 3. Hypotheses, ranked by evidence
- Write two or three candidate mechanisms, each with what it predicts and a cheap observation that would separate it from the others.
- Test the most likely one with the smallest experiment: a print, a debugger breakpoint, a minimal repro, `git bisect`, a unit test of the suspect function. Change one thing at a time.
- A mechanism must explain every symptom. If one symptom is unexplained, the hypothesis is incomplete.

## 4. Fix at the root
- Fix where the wrong thing is created, not where it shows up. Check every caller and every copy of the same pattern.
- Do not add retries, sleeps, broad try/except, null-guards or timeouts to hide an unexplained failure. A retry is valid only when the failure is a known transient (a network blip), and then it is bounded and logged.
- Race conditions and flaky failures: find the shared state and the ordering assumption; do not add a sleep.

## 5. Prove it
- Write a regression test that fails before the fix and passes after. Run it both ways when possible.
- Re-run the original failing command and the full checks. Report what you ran and what it printed.

## 6. Loop discipline (self-correction)
- Given a new error trace or failing test: repeat from step 2 with the new evidence. Do not stack a second patch on a failed first one without understanding why the first failed.
- The same approach failed twice: stop. Write down what you now know for certain, form a new hypothesis, reduce to a minimal repro, or read the library source. Never drop a requirement or weaken an assertion to get green.
- Still stuck after a real attempt: report what you tried, what you ruled out, and the exact next experiment, instead of guessing.

## Report
Root cause in one sentence, the evidence that shows it, the fix, the test that guards it, and anything you could not confirm.
