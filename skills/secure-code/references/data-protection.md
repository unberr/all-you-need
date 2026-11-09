# Data protection and privacy

## Minimize
- Collect, store, log and return only what the feature needs. Do not store what you can derive or do not need (full card numbers, government ids, precise location). Ask what the retention period is and delete on schedule; support user deletion and export where the law applies.
- Responses, logs, analytics events and error reports carry ids, not personal data.

## Sessions
- Generate session ids with a cryptographically secure random source, long and unguessable. Rotate the id on login and on every privilege change (prevents fixation). Invalidate on logout and on password change; server-side expiry plus idle timeout. Bind to the user, not to unchecked client data. Never put session ids in URLs.
- Prefer the framework's session management. Store session data server-side or in signed and encrypted tokens.

## Cookies
- Session and token cookies: `HttpOnly` (not readable by script), `Secure` (HTTPS only), `SameSite=Lax` or `Strict` (`None` only when cross-site is required, with `Secure`), a narrow `Path` and `Domain`, a short lifetime, and the `__Host-` prefix where possible.

## Encryption
- **In transit:** TLS 1.2 or 1.3 everywhere, including service-to-service and database connections. Validate certificates and hostnames; never disable verification. HSTS on public sites. Disable obsolete protocols and weak ciphers.
- **At rest:** encrypt databases, volumes, backups and object storage with managed keys (KMS); field-level encryption for especially sensitive fields. Separate keys from data, rotate keys, restrict who can decrypt.
- Passwords are hashed, not encrypted. See `cryptography.md`.

## Logging and telemetry
- Log security events (login success and failure, permission denials, privilege changes, token creation and revocation, input validation failures at boundaries) with who, what, when, from where, and a request or correlation id.
- Never log passwords, tokens, session ids, API keys, private keys, card numbers, health or other sensitive personal data, full request bodies of sensitive endpoints, or `Authorization` and `Cookie` headers. Redact at the logger, not call site by call site. Keep audit logs append-only and tamper-resistant where compliance needs it. Prevent log injection by encoding newlines and control characters in user-supplied values.
- The same redaction applies to traces, metrics labels, crash reports and analytics.

## Errors
- Users see a short, generic message and a correlation id. Stack traces, SQL, file system paths, internal host names and IPs, framework versions, and cloud details stay in server logs.
- Catch at the boundary, log the detail, return the safe message with the right status code. Fail closed: an error in an authorization check denies access.
- Production: debug off, no exception pages, no directory listings, custom 404 and 500 pages.

## Backups and data lifecycle
- Backups are encrypted, access-controlled, tested by restoring, and covered by the same retention and deletion rules. Test data contains no real personal data.
