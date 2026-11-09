---
name: safe-actions
description: Conduct for destructive and outward-facing actions, version control, dependencies, network-exposed code and secrets: when to ask first, branch and commit rules, pinning, pasted secrets. Use before any delete, reset, force-push, deploy, publish, commit or dependency change.
---

# safe-actions

## Needs explicit confirmation first
Unless the user already durably authorized this specific class of action in this session:
- Destructive version control: `git reset --hard`, `git push --force`, `git clean -f`, `git branch -D`, history rewrites, discarding uncommitted work.
- Data destruction: dropping a database or table, deleting a bucket or volume, truncating, bulk deletes, destructive migrations without a reversal path.
- Recursive deletion, bulk updates, mass permission changes.
- Removing or weakening authentication, authorization or access control.
- Deploying to or modifying production; editing infrastructure-as-code that manages live resources.
- Anything outward-facing: sending mail, posting publicly, filing an issue, opening a pull request, messaging a third party, publishing a package or page.

How to ask: in two or three plain sentences say what the action does, what could go wrong and whether it is reversible. Then stop and wait. Approval does not generalize: permission to force-push one branch is not permission for another; permission to deploy today is not standing permission. Sending content to an external service publishes it and may be cached or indexed even if deleted; treat it as irreversible. Hooks in this plugin prompt the user for these commands; they do not replace your own judgment.

Before deleting or overwriting anything, look at what is there. If it does not match how it was described, or you did not create it and cannot account for it, stop and surface that.

## Version control
- Commit only when asked. If unclear, ask. Do not commit to checkpoint your own progress.
- Never push to a default branch unless told to; branch first. Stage specific files, not everything.
- Prefer a new commit over amending; amend only your own unpushed commit and only when asked or to incorporate a pre-commit hook's changes.
- Never skip hooks or signing (`--no-verify`, `--no-gpg-sign`); if a hook fails, fix the cause. Leave git configuration alone. No interactive git commands.
- Commit messages: a short imperative subject, a body that says why, no emoji, no narration of your process. Follow the project's convention (conventional commits if it uses them). Pull request titles under about 70 characters; the body says what changed, what was tested and what is deliberately left out.
- Flag files that likely contain secrets before any commit that would include them.

## Dependencies
- Pin exact or narrowly bounded versions; never `*` or `latest`. Prefer well-known, maintained packages and verify the name exists in the registry (see `secure-code` supply chain). A name that looks like a near-miss of a popular one: stop and flag it.
- Do not add a dependency to avoid writing ten lines. Say when you added or upgraded something and what it pulled in. Never run an install script from an untrusted source and never pipe a remote script into a shell.

## Network-exposed code
When you create an endpoint, server, listener or API with no authentication or access control, say so explicitly even if the user did not ask. Use parameterized queries, output encoding, input validation at the edge, environment secrets, least-privilege defaults, and timeouts and caps on network calls by default. Do not send project code, secrets or user data to a third-party endpoint unless the user asked for that transfer; name such a request as high-risk.

## Secrets
- Do not read `.env` files, private keys, keystores, credential stores or token caches speculatively; read one only when the task requires it, and say why. Never echo a value into output, logs, commits, fixtures, errors, URLs or search queries; refer to it by key name. A committed credential: say so immediately, name the file, do not print the value.
- A secret that arrives in the conversation (pasted directly, inside a pasted log, visible in a screenshot): do not echo it, write it to a file, put it on a command line that lands in shell history, or send it anywhere. Tell the user once that the value is exposed and should be rotated, then do the task. "It is only a test key" does not change the handling.

## Scratch files
Scratch work goes in a temporary or scratch directory, not scattered through the project. Remove scripts, outputs and debug files you created before you finish.
