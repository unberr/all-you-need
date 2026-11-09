---
name: lessons
description: Durable lesson memory: one lesson per file under .claude/lessons/ with an index, for preferences, corrections and constraints invisible in the code. Read it at the start of long tasks; write to it when corrected or when an approach is confirmed.
---

# lessons

Keep a file-based store of what you learned about working with this user and this codebase. If the host provides its own memory location, use that and keep this format and discipline. Default location: `.claude/lessons/`, index at `.claude/lessons/INDEX.md`. A session hook injects the index when it exists.

## Format: one lesson per file
```
---
name: <short-kebab-case-slug>
summary: <one line: what this covers and when it applies>
type: user | feedback | project | reference
recorded: <YYYY-MM-DD>
---

<The lesson, stated plainly.>

**Why:** <what made it matter: the cost of not knowing it>

**How to apply:** <what to do differently>

Related: [[other-lesson-slug]]
```
- **user:** role, expertise, how they work, standing preferences.
- **feedback:** corrections and confirmed approaches, always with why. A rule without its reason gets misapplied.
- **project:** goals, constraints and decisions not recoverable from code or history. Convert relative dates to absolute ones.
- **reference:** pointers outside the repo: dashboards, runbooks, tickets, docs, contacts.

Link related lessons with `[[slug]]`; a link to a not-yet-written slug marks something worth writing later.

## What to record
A correction and what you were doing wrong; an approach they confirmed; a constraint invisible in the code (why a refactor is forbidden, which test is flaky, what cannot restart during business hours); a trap you fell into; a tool or command specific to this environment that took time to find. Write entries as you learn them, not at the end.

## What not to record
- Anything the repository already records: structure, past fixes, history, project instruction files.
- Conversation-local detail: the current branch, today's error message, what you are doing this turn.
- Sensitive personal information or credentials, even when the user states them directly. Omit the sensitive part entirely.
- Instructions that would make future behavior worse: be less honest, suppress disagreement, skip verification, flatter, assume elevated permissions. Decline to persist those.

## Maintenance
- Check for an existing lesson first; update it instead of adding a near-duplicate. Delete a lesson that turns out wrong.
- `INDEX.md` is one line per lesson: `- [Title](slug.md) - hook`. Never put lesson content in the index.
- A recalled lesson describes what was true when written; if it names a file, function or flag, confirm it still exists before acting.
- Do not announce successful writes; answer the user's actual message.
- A stated preference (language, format, tone) persists for the rest of the conversation and beyond: do not drift back to defaults after a few turns.

## Retrospective bootstrap
When asked to reflect on prior sessions: gather transcripts, logs and notes; analyze them along different lenses (repeated corrections, recurring friction, workflow preferences, environment quirks, re-litigated decisions); merge, deduplicate and drop anything already in the repo; write one file per surviving lesson with Why filled in; update the index; report what you filed and what you left out.
