---
name: devops-release
description: Production readiness: configuration, containers, CI/CD, rollout and rollback, health checks, graceful shutdown, observability, backups, cost, operational impact. Use for Dockerfiles, CI, deploy config, env vars and shipping migrations.
paths:
  - "**/.github/workflows/**"
  - "**/Dockerfile"
  - "**/docker-compose.yml"
  - "**/docker-compose.yaml"
  - "**/compose.yml"
  - "**/compose.yaml"
  - "**/*.tf"
  - "**/Chart.yaml"
---

# devops-release

Code that works on a laptop is not production-ready. Treat the operational side of a change as part of the change.

## Production-ready configuration
- No development-only settings in production: debug off, verbose errors off, no seed or test data, no sample credentials, no open admin tools. Separate configuration per environment, loaded from the environment.
- Every required environment variable is documented (in `.env.example` with safe placeholders and in the README), validated at startup, and named in the failure message without printing the value.
- Secrets come from a secret manager or the platform, never from the repository, the image or CI logs.

## Containers
- Small base image pinned by version or digest, multi-stage build, non-root user, read-only filesystem where possible, no secrets or build tools in the final image, a `.dockerignore` that excludes `.env`, `.git` and local artifacts, an explicit `HEALTHCHECK` or orchestrator probes, resource limits, and handling of `SIGTERM`.
- Logs go to stdout and stderr. State lives outside the container.

## CI/CD
- The pipeline runs the same checks you run locally: build, tests, lint, type check, plus security scans (SAST, dependency and secret scanning, IaC and image scans). Failures block the merge and the deploy. See `secure-code` (`infra-security.md`).
- Deterministic builds: lockfiles, pinned tool and action versions (actions pinned by commit SHA), cached dependencies, no network fetches of unpinned scripts. Build once, promote the same artifact through environments.
- Least-privilege pipeline credentials, short-lived (OIDC) where possible; protected branches; reviewed changes to pipeline files.

## Deploy and roll back
- Choose a rollout strategy that fits the risk (rolling, blue-green, canary) and write down the rollback step. Database migrations are backward compatible with the old and new code during rollout, applied before or alongside the deploy as the strategy requires, and reversible or explicitly one-way with a recovery plan.
- Back up before destructive or irreversible changes and test that the backup restores.
- For a risky behavior change in production, recommend a feature flag or dark launch in the report, with the flag's removal date. This is a rollout tool; it is not a reason to add flags or compatibility shims to internal code.
- Do not run production deploys, data migrations or deletions yourself without explicit approval for that exact action.

## Reliability and observability
- **Health:** a liveness endpoint (the process is up) and a readiness endpoint (dependencies are reachable, safe to receive traffic) that reveal no internals.
- **Graceful shutdown:** (see `performance-reliability`) stop accepting new work, finish in-flight within a deadline, flush, close pools, then exit.
- **Crash handling:** unexpected failures are caught at the boundary, logged with context and a correlation id, return a generic message, and the process restarts cleanly under a supervisor.
- **Logs, metrics, traces:** structured logs without secrets or personal data, rate-errors-duration metrics per endpoint and dependency, tracing across services, alerts on symptoms users feel (error rate, latency, saturation) with a runbook link.
- **Resource monitoring:** CPU, memory, disk, connection pool and queue depth, with alerts before limits are hit.
- Make production issues diagnosable without exposing internals to users: correlation id in the response, detail in the logs.

## Capacity and cost
- Estimate the load a change adds: queries per request, payload size, memory per request, background work, storage growth, third-party API volume and cost. Note rate limits of dependencies. Set limits and budgets; avoid unbounded fan-out, retention and logging volume.

## Backup and recovery
- Define what is backed up, how often, where it is stored and encrypted, who can restore it, and the recovery time and data-loss targets. Restore drills prove it works.

## Document operational impact
Every change that affects operation states, in the report or the PR: new or changed environment variables and defaults, required migrations and their order, new permissions or roles, configuration changes, new dependencies or services, monitoring and alerts to add, the rollout and rollback plan, and the cost or capacity effect.
