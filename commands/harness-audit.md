---
description: Audit this harness for broken skill, hook, command, agent, test, docs, memory and packaging wiring.
---

# /harness-audit

Load the `harness-audit` skill, then run:

```
python3 scripts/harness_audit.py --root . --format text
```

1. Read every finding. This command reports static structure and wiring, not a score or the quality of model output.
2. Fix high-severity findings first. Resolve medium and low findings when they indicate real drift.
3. For a docs finding, update README to match the filesystem. For a hook finding, check that the script exists and fails open. For a memory finding, verify the checkpoint round trip.
4. Rerun the audit and the unit tests.
5. Report the findings fixed and any finding deliberately left, with the reason. Use the deterministic and live evals to discuss behavior.

If the audit reports a missing mechanism that this repository should have, add it with a test rather than suppressing the check.
