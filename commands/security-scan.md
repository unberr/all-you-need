---
description: Scan the harness's own hooks, commands, agents, skills, scripts and settings for security problems.
---

# /security-scan

Load the `secure-code` skill (ai-guardrails reference), then run:

```
python3 scripts/security_scan.py --root . --format text
```

1. Read every finding, including low severity. Confirm or dismiss each one with a reason; do not dismiss a finding because the scanner is "usually noisy".
2. For a confirmed secret, treat it as leaked: remove it, rotate it, and check whether it reached a commit or a log. Deleting the line is not enough.
3. For a pipe-to-shell, unpinned installer or overbroad permission, replace it with a pinned, least-privilege form.
4. For an instruction-injection finding, remove the directive or rewrite it as data the agent must not follow.
5. Rerun the scanner after fixes. End with the score, the findings you fixed and the ones you accepted, each with a reason.

The scanner does not scan MCP configuration. Review hooks, commands, agents, skills and the settings template by hand as described in the skill.
