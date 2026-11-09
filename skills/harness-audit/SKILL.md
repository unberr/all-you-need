---
name: harness-audit
description: Audit this harness for broken structure and wiring, then run behavior evals. Use after changing a hook, skill, command or agent, or before a release.
---

# harness-audit

The harness is code. It needs the same evidence as the code it reviews.

## Run it
```
python3 scripts/harness_audit.py --root . --format text
python3 scripts/harness_audit.py --root . --format json
```

The script is deterministic and uses only the standard library. It reports concrete static findings and exits non-zero for high-severity findings. It does not compute a quality score or grade Claude's output.

## What it checks
- Skills: every `skills/*/SKILL.md` has frontmatter, a name matching its directory, a description of at least 40 characters, and no broken relative references.
- Hooks: `hooks/hooks.json` parses; every referenced script exists; every event has at least one handler; `SessionStart`, `Stop` and `PreCompact` are wired where they should be.
- Commands and agents: frontmatter is present and complete; names match file names.
- Tests: test files exist for every hook and script that carries logic; the suite is discoverable.
- Docs: README mentions every skill, command, agent and hook; counts match the filesystem.
- Memory: the lesson index and task ledger are injected; a pre-compaction checkpoint is written and restored.
- Security: secret, action and config guards are present and wired; the scanner runs clean.
- Evals: deterministic eval scenarios exist and the runner passes.
- Packaging: the plugin manifest validates, has a version, author and icon; the installer parses.
- Hygiene: no cache or OS files in the tree; `.gitignore` covers generated state.

## Reading the result
Read the findings, fix the highest-severity issues, and rerun. Do not use a clean static audit as evidence that a live model task worked.

`--format json` is the machine-readable form. It is stable enough to diff between commits, which is how regressions become visible.

## Manual review the script cannot do
- Read the changed skill or hook as a user would. Is the instruction actionable and non-contradictory?
- Check that a hook fails open: a missing file, malformed input or offline network must not block the session.
- Check that a security rule is not merely documented but enforced by the path a real edit takes.
- Confirm a new command or agent adds a capability, not a second name for an existing one.

## Limits
The audit checks structure and wiring, not whether a skill's advice is correct. It cannot prove that a hook's regex covers every evasion. It does not execute an agent session, so behavior claims still need the eval suite or a manual run.

## Evals: measure changes instead of guessing

A harness change is a hypothesis. An eval is how you find out it is wrong.

### Evals: Two kinds of eval
- Regression evals are deterministic and cheap. They encode a behavior that must not break: the secret guard denies a credential file, the stop gate blocks an unverified edit, the scanner finds a pipe-to-shell, the checkpoint survives a round trip. Run them on every change. Here they live in `evals/` and run with `python3 scripts/run_evals.py`.
- Capability evals are scenarios with graded outcomes: does the agent orient before editing, does it ask one useful question instead of five, does it report an unverified claim honestly. They need a model run and a rubric. Keep them small and review the transcripts; do not average away a failure.

### Evals: Deterministic evals
Each eval is a named scenario with a setup, an action and an observable assertion. The assertion checks output or filesystem state, never the model's opinion.
```
python3 scripts/run_evals.py            # human-readable
python3 scripts/run_evals.py --json     # machine-readable
```
Add an eval when you fix a bug in a hook or guard. The eval should fail before the fix and pass after it. Keep it independent of the network and of the current directory.

### Evals: Capability scenarios
Write each scenario with:
- the task, as the user would phrase it;
- the starting repository state;
- what a correct run must do, in observable terms;
- what must not happen (an unrequested edit, a skipped test, a secret in the reply);
- the grading rule: pass, partial or fail, with a reason.

Run each scenario more than once when the behavior is nondeterministic. Report the pass count and the failures, not a single lucky run. A scenario that passes because the model guessed is not evidence.

### Evals: Rules
- Do not edit an eval's assertion to make a failing change pass. Fix the change or record the regression.
- Do not compare runs from different prompts, models or repository states without saying so.
- Keep the deterministic suite under a minute. Slow evals stop being run.
- Report the command, the count and the exact failures. State what the eval cannot cover.
- An eval that never failed has not been shown to work. Introduce a deliberate fault once and confirm it is caught.

### Evals: Reporting
```
Evals: 5/5 passed
- secret-guard denies .env: PASS
- stop-gate blocks unverified edit: PASS
- scanner finds pipe-to-shell: PASS
- checkpoint round trip: PASS
- slop lint flags any: PASS
Not covered: whether a skill improves a real agent session; that needs a graded capability run.
```
