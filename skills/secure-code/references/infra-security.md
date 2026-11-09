# Infrastructure, deployment and operations security

## Configuration and secrets
- Production configuration differs from development: debug off, verbose errors off, test accounts and seed data removed, default credentials changed, sample apps and admin consoles removed. Separate dev, test, staging and production environments, each with its own credentials and data.
- Secrets live in a secret manager or the platform's secret store (Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, Kubernetes secrets with encryption at rest), injected at runtime as environment variables or mounted files. Not in the repository, image layers, build logs, CI output, `docker-compose.yml`, Terraform state in plain form, or frontend bundles. Provide `.env.example` with safe placeholders and keep `.env` in `.gitignore`.
- Validate required environment variables at startup and fail fast with a message that names the variable, never its value.
- Rotate on a schedule and immediately after exposure. A committed secret is compromised even after deletion: rotate it, then remove it from history.

## Least privilege
- Application database users have only the rights they need (no superuser, no schema changes at runtime; separate migration credentials). Cloud roles and API tokens are scoped to specific resources and actions. Service accounts per service. No wildcard IAM (`*`) permissions without a reason written down. Short-lived credentials (workload identity, OIDC from CI) over long-lived keys.
- Network: private subnets for databases and internal services, security groups and network policies that allow only needed flows, no public database or admin ports, deny-by-default egress where practical.

## Containers
- Minimal base images (distroless, slim, alpine where suitable), pinned by digest, rebuilt regularly. Run as a non-root user, read-only root filesystem, drop capabilities, no `--privileged`, no host mounts of sensitive paths, resource limits, no secrets baked into layers, multi-stage builds so build tools do not ship. Scan images (Trivy, Grype). Handle `SIGTERM` for graceful shutdown.

## CI/CD
- Run on every change, for AI-written and human-written code alike: tests, linters, type checks, SAST (Semgrep, CodeQL), dependency scanning/SCA (OSV-Scanner, `npm audit`, `pip-audit`, Dependabot), secret scanning (gitleaks, trufflehog, platform secret scanning with push protection), IaC scanning (Checkov, tfsec, Trivy config), and container scanning. Gate merges on failures.
- Protect the pipeline: least-privilege tokens, protected branches, required reviews, no secrets to pull-request builds from forks, pinned third-party actions, signed artifacts and provenance where the stakes justify it.

## Transport and edge
- TLS everywhere with current protocol versions, valid certificates, automated renewal. HTTP redirects to HTTPS with HSTS. Security headers at the proxy or app. A WAF or rate limiting at the edge for public APIs.

## Observability and response
- Structured logs, metrics and traces without secrets or personal data. Alerts on authentication failures, privilege changes, error spikes and anomalous access. Health and readiness endpoints that reveal no internals. Keep logs long enough to investigate and short enough to respect privacy rules.
- Backups encrypted, access-controlled and restore-tested. A documented rollback and incident procedure.

## Deployment safety
- Migrations backward compatible with the running version; reversible or explicitly one-way with a documented recovery. Staged rollout (canary, blue-green) for risky changes, with a rollback path; recommend a feature flag or dark launch for risky production behavior changes in the report, as a rollout tool that is removed afterwards.
