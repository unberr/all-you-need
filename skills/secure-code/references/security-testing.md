# Security testing

Test the requirement, not the implementation. A security test must fail when the control is removed.

## What to write for every endpoint or feature that handles access or untrusted input
- **Authentication:** unauthenticated request is rejected (401); expired, malformed, tampered, wrong-audience and `alg: none` tokens are rejected; a logged-out or revoked session is rejected.
- **Authorization:** each role gets exactly the allowed actions. Regular user cannot call admin routes (403). **IDOR:** user A requests user B's resource id for read, update, delete, download and nested resources; expect 403 or 404 and no data. Tenant isolation: a tenant-A user cannot see tenant-B rows through any route, search, export or bulk endpoint. Privilege escalation through mass assignment (`role`, `isAdmin`, `ownerId`).
- **Injection and malformed input:** SQL and NoSQL metacharacters, shell metacharacters, template syntax, oversized bodies, deeply nested JSON, wrong types, null bytes, unicode tricks, negative and huge numbers, duplicated parameters. Expect rejection or inert handling, never a 500 with internals.
- **XSS and output encoding:** stored and reflected payloads come back encoded.
- **SSRF and path traversal:** internal addresses, cloud metadata addresses and `../` sequences are refused.
- **File upload:** wrong type, oversized, double extension, path in the file name, archive with `..`.
- **Rate limiting and brute force:** repeated login or reset attempts hit the limit.
- **CSRF and CORS:** a cross-origin state-changing request without the token fails; disallowed origins get no CORS headers.
- **Business logic abuse:** negative quantities, price tampering, replaying a request (idempotency), skipping steps in a flow, race conditions on balances and coupons (concurrent requests).
- **Error responses and logs:** errors expose no stack traces or paths; logs contain no passwords or tokens (assert on captured log output).
- **Headers and cookies:** the security headers and cookie flags are present on real responses.

## Make them regressions
- Each fixed vulnerability gets a test that reproduces the exploit and passes after the fix. Name it for the requirement.
- Mutation check: remove the control, confirm the test fails, restore it.

## Automated validation
- Run SAST (Semgrep with the project's rule sets, CodeQL, Bandit, gosec, Brakeman), dependency scanning (OSV, `npm audit`, `pip-audit`, `cargo audit`, `govulncheck`), secret scanning (gitleaks, trufflehog), IaC and container scans, and a DAST or API fuzzer (OWASP ZAP, schemathesis) against a test environment when the stakes justify it. Read the results, fix or explain each, and say which scanners you could not run.

## Review
- AI-generated security tests get a human review: they tend to confirm what the code does instead of what it must do. Report them as unreviewed.
