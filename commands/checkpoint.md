---
description: Write a durable checkpoint of the current goal, changes, checks and open items before a long pause.
---

# /checkpoint

Write or update `.all-you-need/checkpoint.md` so a later session can resume without guessing. The `PreCompact` hook does this automatically before compaction; run this command when you want a checkpoint at a chosen point.

Use this format, bounded to roughly 150 lines:
```
# Session checkpoint
Written: <absolute date and UTC time>
Trigger: manual
Working directory: <absolute path>

## Goal
<the current request in one or two sentences>

## Decisions
- <decision and the reason it was made>

## Files changed
- `path/to/file` - what changed and why

## Checks run
- PASS|FAIL: `<command>` (exit code, first actionable output)

## Open items
- [ ] <remaining work, in order>

## Next action
<the single next thing to do, specific enough to start without rereading the transcript>

## Unverified
- <claim or area not checked, or "nothing">
```

Rules:
- Do not copy tool output, secrets, tokens or personal data into the checkpoint.
- Mark inferences as inferences. A plan is not a result.
- Verify the file list against `git status` when this is a git repository.
- Do not tick an open item that has not been verified.
