---
name: finish-the-job
description: Complete long or multi-part tasks in full: keep a task ledger that survives context compaction and blocks stopping with items open. Use for tasks with more than three steps, long prompts, many files or bulk changes.
---

# finish-the-job

Long tasks fail in predictable ways: parts get skipped, output is cut short with "the rest is similar", work stops at a natural pause, or state is lost when the context is compacted. This skill closes each gap. It cannot raise the context limit; it makes sure nothing is lost when the limit is hit.

## 1. Write the ledger before doing anything
Create `.all-you-need/tasks.md` in the project root (add `.all-you-need/` to `.git/info/exclude` so it is never committed). Format:

```
# Task ledger
Goal: <the user's request, copied verbatim or near-verbatim>
Constraints: <rules the user stated that every item must respect: language, framework, version, style, do-not-touch areas>
- [ ] 1. <concrete, checkable item>
- [ ] 2. <next item>
```

- Split the request into items you can verify one by one: one file, one function, one requirement, one chunk of input. A vague item ("improve the code") is not an item.
- Every explicit requirement in the prompt becomes an item. Re-read the prompt line by line; do not work from memory of it.
- Hooks read this file. After a context compaction or resume it is re-injected automatically. While any `- [ ]` item is open, stopping the turn is blocked as long as you keep making progress.

## 2. Work the ledger
- Take items in order. Finish one completely (code, tests, checks) before starting the next.
- Tick `- [x]` the moment an item is truly done and verified, not before. Never tick an item to get past the stop hook.
- Item cannot be done (missing access, genuinely ambiguous, blocked): mark `- [!] n. <item> (blocked: <reason>)`. A blocked item is reported to the user, never dropped silently.
- New work discovered mid-task: add it as an item. Never reduce scope without telling the user.

## 3. Never shorten the output
- No "and so on", "similar for the rest", "remaining files unchanged" in place of real work. Do each one.
- Output too large for one reply: split it across files or turns and say so, with the ledger tracking which part is done. Do not truncate and do not summarize in place of the deliverable.
- Do not leave placeholders, stubs or `...` in code you wrote.

## 4. Large inputs
- A long document, big log or many files: process in chunks. Record each chunk in the ledger when done (`- [x] lines 1-400`). Do not skim and then claim full coverage.
- Many independent pieces: hand them to subagents, one item each, then check each result yourself before ticking it.
- Search or read results that are cut off: narrow the query or page through, and record the bounds you covered.

## 5. Context pressure
- Context getting large is not a reason to hurry, abbreviate or stop. Finish the current item, update the ledger, and carry on. The ledger holds the state, so a compaction costs nothing.
- After a compaction or a resume, read the injected ledger first, then continue at the first open item. Do not restart finished items and do not re-ask the user questions the ledger already answers.
- Keep ledger items short. Put long notes (decisions, file paths, partial results) in the lines under the item, not in your memory.

## 6. Close out
Before the final reply:
1. Re-read the user's original request, the Constraints line and the ledger side by side; confirm no earlier constraint was forgotten. Every requirement maps to a ticked item or a `[!]` with a reason.
2. Run the project's checks (see `all-you-need`).
3. Final reply: what was done, what is blocked and why, and `Not verified:` line. Name any item you ticked but could not fully check.
4. When all items are ticked, delete `.all-you-need/tasks.md`.

## What this does not do
It does not extend the context window and cannot force a stop to continue after you stop making progress: the stop gate gives up when an attempt closes no open item, so it can never trap a session. If a task is truly too big for the time or access you have, say exactly what remains rather than implying it is finished.
