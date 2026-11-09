---
name: delegation
description: When and how to hand work to subagents, run independent investigations in parallel, and batch tool calls. Use when a task spans many files, has independent pieces, needs a broad mechanical sweep, or when reading would flood the context.
---

# delegation

## When to delegate
- Answering means reading across many files and you need the conclusion, not the contents.
- Several independent investigations can run at once.
- A broad mechanical sweep: every call site, every config, every suite.
- The work would flood your context with material you do not need to keep.

Do not delegate when you already know the file and the symbol (just look), or to avoid thinking about something hard. Do not delegate something and then also do it yourself: wait for the result.

## Brief the subagent completely
It cannot see your conversation. Give the goal, constraints, paths, the definition of done, and the shape of the answer you want. State whether it may edit files; give writers disjoint files. Launch independent agents together in one message so they run concurrently.

## Use the reports critically
A subagent report is not shown to the user: relay what matters in your own words. A subagent can be confidently wrong, miss context you have, or drift from the task: spot-check the claims you will rely on, and correct, re-scope or stop one that goes off track. If another agent or a reviewer contradicts you, check before accepting; adjust if they are right, say why if they are wrong. Never predict or fabricate a pending agent's findings.

## Batch your own calls
Independent tool calls go in one message; calls whose input depends on an earlier output go in separate messages. Plan a few steps ahead so speculative reads ride along with the certain ones: reading six files takes one message. Over-fetching context is almost always cheaper than another round trip.

## Cost
Fan-out has a price. Use it when the task needs the scale (a migration across hundreds of sites, an audit too large for one context, a decision that deserves independent adversarial review). When it would help but the user has not asked, say briefly what it involves and let them decide. Give verifiers distinct lenses rather than identical copies (see `references/rigor.md`).
