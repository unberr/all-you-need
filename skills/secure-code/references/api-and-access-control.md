# API and access control

## Exposure
- Inventory every route before finishing. Internal, admin, health-with-detail, metrics, debug, profiling, API-docs and test endpoints are not public: require authentication and an admin role, bind them to an internal interface, or do not ship them. Production builds have debug mode, verbose errors, interactive consoles (Werkzeug, Django debug toolbar, Spring Actuator `env`/`heapdump`, GraphQL introspection and playground, Swagger UI) turned off or protected.
- No security through hidden URLs. A route not linked in the UI is still reachable.
- Do not return fields the caller does not need (password hashes, internal ids, tokens, other users' data, internal state). Build response objects explicitly from an allowlist; never serialize a database model wholesale.

## Authentication
- Every protected endpoint requires valid authentication, checked server-side by shared middleware or a decorator that is on by default, so a forgotten annotation fails closed.
- Use a proven framework or identity provider and standard protocols (OIDC, OAuth 2.0 with PKCE, SAML). No custom password or token schemes. MFA for privileged accounts and sensitive actions.
- Login, password reset and token endpoints: rate limit per account and per IP, generic error messages that do not reveal whether the account exists, constant-time comparison, lockout or backoff after repeated failure, single-use expiring reset tokens.
- Passwords: Argon2id (bcrypt or scrypt where Argon2id is unavailable), unique salt, never plaintext or reversible encryption.

## Authorization
- Check permission on every request and every object on the server. The UI hiding a button is not authorization.
- **Deny by default.** Add explicit allow rules. A missing rule means no access.
- **Resource-level checks (prevent IDOR):** never treat a client-supplied id as proof of access. Load the object scoped to the caller (`WHERE id = ? AND owner_id = ?`), or load it and check ownership or tenant membership before use. Applies to read, update, delete, download, export, nested resources and bulk endpoints. Unpredictable ids help but are not authorization.
- **Roles and permissions (RBAC/ABAC):** define roles centrally, check capabilities not role names scattered in code, keep privilege-changing endpoints admin-only, and re-check after the role changes. Multi-tenant: every query is tenant-scoped, enforced in one place (row-level security, a scoped repository).
- Prevent mass assignment: bind only allowlisted fields from request bodies; users cannot set `role`, `isAdmin`, `ownerId`, `price`.
- Prevent privilege escalation: horizontal (user A to user B) and vertical (user to admin) paths both tested.

## Tokens
- **JWT:** verify the signature with a pinned algorithm (never accept `none` or let the token choose the algorithm), check `iss`, `aud`, `exp`, `nbf`, keep lifetimes short, use refresh-token rotation, keep the signing key server-side, and support revocation for sensitive flows. Do not put secrets or sensitive data in the payload; it is only encoded.
- API keys: hashed at rest, scoped, rotatable, never in URLs or logs.

## Abuse protection
- **Rate limiting** on authentication, expensive and enumerable endpoints, with limits per user, per IP and per token, returning 429 with `Retry-After`. Use the framework's or gateway's limiter, shared across instances.
- Request size limits, JSON depth limits, pagination caps, query complexity limits (GraphQL depth and cost), upload limits, and timeouts on every request and outbound call.

## Browser-facing controls
- **CORS:** an explicit allowlist of trusted origins. Never `Access-Control-Allow-Origin: *` with credentials, never reflect the request `Origin` unchecked, allow only the methods and headers needed.
- **CSRF:** for cookie-authenticated state-changing requests, use anti-forgery tokens plus `SameSite` cookies, check `Origin`/`Referer`, and never change state on `GET`. Token-in-header APIs (Authorization header, not cookie) are not CSRF-exposed.
- **Security headers:** `Content-Security-Policy` (no `unsafe-inline` where avoidable), `Strict-Transport-Security` (with `includeSubDomains` once all subdomains are HTTPS), `X-Content-Type-Options: nosniff`, `Referrer-Policy`, `Permissions-Policy`, framing control via CSP `frame-ancestors` (and `X-Frame-Options` for old browsers), `Cache-Control: no-store` on sensitive responses. Use the framework's helper (helmet, Django `SecurityMiddleware`, ASP.NET middleware).

## API design
- Correct methods (`GET` safe and cacheable, `POST` create, `PUT`/`PATCH` update, `DELETE`), correct status codes (401 unauthenticated, 403 forbidden, 404 for resources the caller should not know exist, 422 or 400 for invalid input, 429 throttled), consistent error envelope without internals, schema validation of every request and response.
