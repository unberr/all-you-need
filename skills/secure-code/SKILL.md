---
name: secure-code
description: Security by default: threat modeling, authn/authz, input handling and injection, secrets, crypto, data protection, API and frontend security, supply chain and CVEs, infra, security tests, AI guardrails. Use for any code touching input, auth, files, shell, SQL, HTML, dependencies or deploys.
---

# secure-code

Secure by default in the first draft, not as a later pass. A CVE belongs to a library version, so check versions; the rest is patterns, design and verification.

## 1. Before writing code
- Anything with authentication, authorization, money, personal data, uploads, outbound requests or a new public endpoint: do a short threat model (assets, trust boundaries, attackers, abuse cases). Read `references/threat-modeling.md`.
- Check dependencies first (section 2). Never guess a package or a version.

## 2. Dependencies: verify, then use
- Confirm every package exists in its registry and is the one intended (hallucinated and typosquatted names are an attack). Confirm the version has no known advisories. Check the license. A hook does this when manifests and lockfiles change; do it by hand for anything else. Details and commands in `references/supply-chain.md`.
- Read the installed version from the lockfile or environment, never assume the latest. If a check cannot run (offline), say the versions are unchecked; never report "no CVEs" without a result.
- Manual OSV query: `curl -s -X POST https://api.osv.dev/v1/query -d '{"package":{"name":"<name>","ecosystem":"<PyPI|npm|crates.io|Go>"},"version":"<version>"}'`
- The model's memory of vulnerabilities is stale. OSV output and current docs are the source.

## 3. Write it safely (load the reference for the work at hand)
| Work | Read |
| --- | --- |
| Endpoints, auth, roles, IDOR, rate limits, CORS, CSRF, JWT, headers, exposed routes | `references/api-and-access-control.md` |
| Validation, SQL and command injection, XSS, SSRF, paths, uploads, deserialization, LLM input | `references/input-output.md` |
| Sessions, cookies, encryption, logging, error messages, personal data, retention | `references/data-protection.md` |
| Hashing, encryption, signatures, tokens, random values, TLS | `references/cryptography.md` |
| Browser code, tokens, CSP, postMessage, third-party scripts, secrets in bundles | `references/frontend-security.md` |
| Packages, versions, licenses, provenance | `references/supply-chain.md` |
| Containers, CI/CD, cloud permissions, secrets management, deployment | `references/infra-security.md` |
| Prompt injection, secrets in context, agent permissions, reviewing legacy code | `references/ai-guardrails.md` |
| Tests for access control, injection, abuse and regressions | `references/security-testing.md` |

## 4. Core rules that always apply
1. Treat all external input as untrusted: validate type, length, format and range with an allowlist at the boundary; encode output for its context.
2. Parameterized queries, argument-list process calls, auto-escaping templates. Never build SQL, shell, HTML, LDAP or XPath from strings with input.
3. Authenticate and authorize on the server, on every request and every object. Deny by default. A client-supplied id is never proof of access.
4. No secrets in source, frontend bundles, fixtures, logs, URLs, memory notes or commits. Configuration comes from the environment or a secret manager, with `.env.example` placeholders.
5. Modern cryptography only: Argon2id for passwords, AES-GCM or ChaCha20-Poly1305, Ed25519 or ECDSA, CSPRNG for tokens. Reject MD5, SHA-1, DES, ECB, weak RNGs and home-made crypto.
6. TLS everywhere with verification on. Secure cookie flags. Security headers and a CSP. Explicit CORS allowlist.
7. Errors return generic messages with a correlation id. No stack traces, SQL, paths or infrastructure details to users. Fail closed.
8. Never log passwords, tokens, keys or sensitive personal data. Collect and return only what the feature needs.
9. Least privilege for users, services, database accounts, containers and cloud roles.
10. Rate-limit and size-limit anything an anonymous caller can reach. Timeouts on every outbound call.
11. No debug, admin or diagnostic endpoint reachable in production without authentication.
12. Do not rely on obscurity or client-side checks. Reuse vetted libraries for security controls.

## 5. Security self-audit before you finish
Walk the final change against this list and report any gap:
exposed or unprotected endpoints; missing authentication or authorization on any path; IDOR via client-supplied ids; secrets or tokens in code, logs or the client bundle; injection sinks; unescaped output; unsafe deserialization; SSRF and path traversal; upload handling; weak or custom crypto; sessions and cookies; CORS and CSRF; verbose errors; unbounded input or missing rate limits; new dependencies verified; permissions wider than needed; tests that cover the abuse cases.

## 6. Report
- Which dependencies were checked and what the registry and OSV returned, or that a check could not run.
- Assumptions, residual risk, and anything that needs a human.
- Flag security-critical changes (authentication, authorization, cryptography, secrets, permissions, payments, deployment) with `Security review needed: <what to check>`. A hook requires that line when such files are edited. Never call AI-written security code audited.
- Label every security claim: verified (ran or read it), believed, unknown. A suspected vulnerability needs trigger, wrong result and location; otherwise it is a suspicion.
