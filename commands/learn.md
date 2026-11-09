---
description: Turn a correction or confirmed approach from this session into one durable lesson file.
---

# /learn

Load the `lessons` skill.

1. Identify the lesson from this session: a correction the user made, an approach they confirmed, a project constraint that is not visible in the code, or a trap that cost time.
2. Search `.claude/lessons/` for an existing lesson on the same point. Update it instead of adding a near-duplicate.
3. Write exactly one file at `.claude/lessons/<slug>.md` with the frontmatter and three sections from the skill: the lesson, `**Why:**` and `**How to apply:**`. Use an absolute date.
4. Add one line to `.claude/lessons/INDEX.md`: `- [Title](slug.md) - hook`.
5. Do not record credentials, personal data, conversation-local detail, or an instruction that would make future work less honest or less careful.
6. Report the file you wrote in one sentence. Do not paste the lesson back into the conversation.

If the session contains no durable lesson, say so and write nothing.
