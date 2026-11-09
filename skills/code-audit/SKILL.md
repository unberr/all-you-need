---
name: code-audit
description: Master code audit checklist in 20 sections (recon, secrets, auth, injection, API, DB, mobile, crypto, supply chain, infra, privacy and more). Use to audit, security-review or harden a codebase, or on /code-audit.
---

# Code audit

Run this procedure against the current codebase (or the path the user names).

1. First, identify what this app is: frontend, backend, full-stack, mobile, CLI or library; its languages, frameworks, database and hosting; and its features (user accounts, payments, file uploads, AI, email, realtime, background jobs).
2. Tell the user which sections and tagged items apply and which you are skipping, with a one-line reason for each skip.
3. Audit only what applies. For each issue give: severity (critical / high / medium / low), file and line, what an attacker or bug could do, and the fix.
4. Sort findings by severity. Do not change any code until the user approves.
5. List anything you could not verify from the code alone (live server, cloud console, account settings) so the user can check it themselves.
6. Only use the High-security tier (section 20 and items tagged High-security) if the user asks for it or the app clearly handles highly sensitive data.

Every section opens with an "Applies to" line, and conditional items carry a tag (like Frontend: or Docker:). Never apply a tagged item to an app that does not match the tag.

Tooling to use where it fits (all installed): trailofbits static-analysis (semgrep, codeql), insecure-defaults, sharp-edges, supply-chain-risk-auditor, entry-point-analyzer, audit-context-building, fp-check (verify each finding before reporting), claude-security. Before reporting a finding, try to refute it (harness Section 20.1) and give a concrete failure scenario (20.2).

## Evidence bar (merged from security-audit)

- A finding needs all six: the lower-trust principal, the input or action it controls, the intended control, the boundary crossed, the affected principal or resource, and the concrete result. Missing one: it is a hardening note, not a finding.
- Not findings: checklist deviations, defense-in-depth advice with no reachable violation, self-impact, intended same-principal authority, a parser crash with no boundary result.
- A control that lives outside the repo (proxy, provider setting, IAM policy, header config) is `needs validation`: name the exact missing fact and a safe way for the owner to check it. Never guess it present or absent. `needs validation` items get no severity.
- Severity anchors. **Critical**: unauthenticated code execution, full data-store access, or arbitrary account takeover. **High**: fully defeats an explicit control with real consequences (auth bypass, cross-tenant read or write, stored XSS on other users, authenticated RCE). **Medium**: real violation with narrow blast radius or uncommon preconditions. **Low**: non-secret internals, or high effort for minimal gain. Severity never exceeds the demonstrated impact.
- Fix: name the invariant and the narrowest change at the last trusted decision point, plus the regression test that would catch it.
- Execution safety: source reading is read-only. Run target code (tests, builds, PoCs) only in the sandbox, with no network, dummy principals and secrets, and stop at the minimum effect that proves the defect. Never probe deployed endpoints, shared services or real accounts.

## Full audit mode

Only when the user asks for a full, comprehensive or end-to-end audit, or for report files. Otherwise use the checklist below in guidance mode and write no artifacts.

For supply-chain and cloud companions, use the local `secure-code` references (`supply-chain.md`, `infra-security.md`) and the repo's own scripts. External third-party audit packs are not required.

- Web, auth, sessions, CSRF, SSRF: `WEB-PROTOCOL-AND-AUTH.md`; browser code: `CLIENT-SIDE.md`
- Multi-tenant data, retention, deletion: `DATA-ISOLATION-AND-LIFECYCLE.md`
- Cloud, IaC, containers: `CLOUD-AND-DEPLOYMENT.md`; build and release: `SUPPLY-CHAIN-AND-RELEASE.md`
- RPC, queues, websockets: `PROTOCOLS-RPC-AND-MESSAGING.md`; DoS limits: `RESOURCE-EXHAUSTION-AND-AVAILABILITY.md`
- C, C++, unsafe Rust, parsers of binary formats: `MEMORY-SAFETY-AND-BINARY.md`
- Desktop, mobile, local IPC: `DESKTOP-MOBILE-AND-LOCAL-IPC.md`; LLM features: `AI-AND-LLM.md`
- Attack class reference for every run: `ATTACK-CLASSES.md`

## Checklist

1. Recon and threat model
Applies to: every app.
[ ] Identify the stack, features and where the app is deployed
[ ] Map every entry point: routes, forms, APIs, webhooks, cron jobs, websockets, queues
[ ] Classify all data by sensitivity: public, internal, confidential, secret
[ ] Build a threat model (STRIDE): who would attack, what they want, what they could realistically do
[ ] Map trust boundaries, every place data crosses between systems or privilege levels
[ ] List what a logged-out user can access or do
[ ] List what a regular user can do that only an admin should
[ ] Trace user input from the form to the server to the database and back to the screen
[ ] Find every place that trusts the frontend instead of verifying on the server
[ ] Assume one component is compromised and show how far an attacker could get
[ ] Identify single points of failure, technical and human
2. Secrets, environment and configuration
Applies to: every app.
[ ] Find hardcoded API keys, passwords and tokens in the code
[ ] Check environment variables: all documented, none with unsafe defaults
[ ] Make sure .env files are gitignored and never committed or deployed
[ ] Scan the full git history for leaked secrets (gitleaks, trufflehog)
[ ] Separate dev, staging and production configs
[ ] Turn off debug mode and verbose errors in production
[ ] Move hardcoded values that should be config into config
[ ] Remove default credentials, test accounts and leftover test or debug routes
[ ] Remove console.logs and debug code
[ ] Have a plan to rotate every secret if one leaks; prefer short-lived credentials
[ ] Frontend: check which env variables end up in the client bundle (NEXT_PUBLIC_, VITE_, REACT_APP_)
[ ] Frontend: search the built JavaScript for API keys
[ ] Web: check for exposed files on the live site: .git folder, .env, .bak and .old files, .DS_Store, phpinfo, public source maps
[ ] Web: check robots.txt and the sitemap for revealed admin paths
3. Authentication and sessions
Applies to: apps with user accounts or logins.
[ ] Use a well-known auth library or provider instead of custom login code
[ ] Hash passwords with Argon2, bcrypt or scrypt
[ ] Add brute-force protection on login (lockout or growing delays)
[ ] Prevent user enumeration: login, signup and reset messages must not reveal whether an email exists
[ ] Secure the password reset flow: single-use, expiring tokens; reset links built from config, not the Host header
[ ] Check the email verification flow
[ ] Add session expiration and "log out of all devices"
[ ] Invalidate all sessions after a password change
[ ] Prevent session fixation (new session ID after login)
[ ] Set cookie flags: HttpOnly, Secure, SameSite
[ ] Offer 2FA; require passkeys or hardware keys for admins
[ ] Normalize usernames to block lookalike (homoglyph) impersonation
[ ] Frontend: don't keep auth tokens in localStorage when HttpOnly cookies are an option
[ ] JWT: reject alg none, use a strong secret, short expiry and refresh token rotation
[ ] OAuth / social login: validate the state parameter and redirect URIs, use PKCE
4. Authorization and access control
Applies to: apps with user accounts, roles or private data.
[ ] Check permissions on the server for every route and endpoint, not just in the UI
[ ] Protect admin routes
[ ] Re-check authorization on every request, not only at login
[ ] Prevent IDOR: users can't reach other users' data by changing an ID in the URL or request
[ ] Prevent mass assignment: users can't set fields like role, isAdmin or ownerId through the request body
[ ] Give each role the least privilege it needs
[ ] Make sure soft-deleted data never shows up anywhere
[ ] Keep an audit log of admin actions
[ ] Multi-tenant apps: one customer or organization can never see another's data
[ ] Admin panel: add extra protection (separate login, IP allowlist, phishing-resistant MFA)
[ ] Supabase: enable and test row level security on every table
[ ] Firebase: review Firestore and Storage security rules
5. Input handling and injection
Applies to: any server-side code that handles user input.
[ ] Validate all input on the server (type, length, format), not just in the frontend
[ ] Sanitize form input
[ ] Prevent SQL and NoSQL injection with parameterized queries everywhere
[ ] No eval, new Function or other dynamic code execution on user input
[ ] Prevent command injection wherever shell commands run
[ ] Prevent path traversal in file paths built from user input
[ ] Prevent SSRF wherever the server fetches a user-supplied URL
[ ] Prevent open redirects
[ ] Prevent server-side template injection
[ ] Prevent insecure deserialization
[ ] Prevent HTTP header and CRLF injection
[ ] Prevent log injection
[ ] Check regexes for ReDoS (patterns that freeze the server on crafted input)
[ ] Check business logic: negative quantities, skipping steps in multi-step flows
[ ] Check race conditions: coupons used twice, double spending, double submits
[ ] Test with empty, extremely long, emoji and unicode input
[ ] XML parsing: disable external entities (XXE)
[ ] JavaScript / Node: check for prototype pollution
6. Browser and frontend security
Applies to: web apps with a browser frontend.
[ ] Prevent XSS: check every place user content is rendered, plus dangerouslySetInnerHTML, v-html and innerHTML
[ ] Add CSRF protection on state-changing requests
[ ] Add security headers: Content-Security-Policy, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
[ ] Block clickjacking (frame-ancestors or X-Frame-Options)
[ ] Check CORS: explicit origin allowlist, never a wildcard with credentials
[ ] Enforce HTTPS everywhere with no mixed content
[ ] Add rel="noopener noreferrer" to links that open new tabs
[ ] Validate the origin in every postMessage handler
[ ] Add subresource integrity to scripts loaded from CDNs
[ ] Review third-party scripts, embeds and analytics
[ ] Make sure private pages and API responses aren't cached by a CDN or browser (Cache-Control)
[ ] Prevent double-click submits from creating duplicates
[ ] Add loading, error and empty states; handle slow networks and offline
[ ] Check accessibility, mobile responsiveness and SEO basics
[ ] SSR frameworks (Next.js, Nuxt, SvelteKit, Remix): no user data leaking between requests through module-level variables
[ ] SSR frameworks: server-only code and secrets are never imported into client components
[ ] SSR frameworks: fix hydration mismatches
7. APIs and backend
Applies to: apps with a server, API or serverless functions.
[ ] Secure every endpoint with both authentication and authorization
[ ] Add rate limiting per user and IP, strictest on login, signup, password reset and expensive endpoints
[ ] Limit request body size
[ ] Add pagination to list endpoints
[ ] Add timeouts to incoming requests
[ ] Return a consistent error format with no stack traces or internal details
[ ] Version the API
[ ] Verify signatures on every incoming webhook
[ ] Add a health check endpoint
[ ] Disable unused HTTP methods and routes
8. Database and data integrity
Applies to: apps with a database.
[ ] Make sure the database isn't reachable from the internet and uses strong credentials
[ ] Use SSL for database connections
[ ] Give the app's database user least privilege
[ ] Use transactions for multi-step writes
[ ] Add unique constraints to prevent duplicate records
[ ] Add validation at the schema level, not only in app code
[ ] Use optimistic locking where two people can edit the same record
[ ] Add indexes for slow queries and fix N+1 queries
[ ] Find unbounded queries that could return millions of rows
[ ] Check connection pool limits
[ ] Check migrations for destructive changes
[ ] Encrypt sensitive fields at rest
[ ] Store dates in UTC and handle time zones and DST correctly
[ ] Set data retention rules and delete what you no longer need
9. Feature-specific checks
Applies to: only the features your app actually has. Skip every subsection that doesn't match.
File uploads
[ ] Validate file type by content (magic bytes), not just the extension, and cap file size
[ ] Store uploads outside the web root and make sure they can never be executed
[ ] Serve uploads from a separate domain, or with Content-Disposition and nosniff headers
[ ] Block or sanitize SVGs, which can contain scripts
[ ] Protect against zip bombs and decompression-bomb images
[ ] Prevent zip slip when extracting archives
[ ] Strip EXIF metadata (it can contain users' GPS locations)
[ ] Serve private files through short-lived signed URLs
Payments
[ ] Confirm payments on the server through webhooks, never from the success redirect page
[ ] Never trust prices or totals sent from the client
[ ] Use idempotency keys so nothing is charged twice
[ ] Store money as integers (cents), never floats
[ ] Handle refunds, failed payments and subscription changes from webhooks
[ ] Never store raw card numbers; use the provider's hosted fields
AI / LLM features
[ ] Check for prompt injection, including indirect injection through documents or web pages the AI reads
[ ] Make sure users can't extract the system prompt or other users' data
[ ] Limit which tools and actions the AI can take on a user's behalf
[ ] Treat AI output as untrusted: sanitize it before rendering HTML or running it
[ ] Add per-user rate limits and spending caps on AI calls
Email
[ ] Set up SPF, DKIM and DMARC on the domain
[ ] Prevent email header injection in contact forms
[ ] Rate limit outgoing email so the app can't be used for spam
Realtime and websockets
[ ] Authenticate websocket connections and check their origin
[ ] Authorize every channel or subscription
[ ] Limit message size and rate
GraphQL
[ ] Disable introspection in production
[ ] Add query depth and complexity limits
[ ] Limit batching and aliases
[ ] Enforce authorization per field, not just per query
Background jobs and cron
[ ] Move slow tasks to a background queue
[ ] Make sure cron jobs can't overlap or run twice
[ ] Make retried jobs idempotent
10. Mobile apps
Applies to: iOS and Android apps only.
[ ] Keep secrets out of the app binary, since anyone can decompile it
[ ] Store keys in the iOS Keychain / Secure Enclave or Android Keystore / StrongBox
[ ] Use App Attest or Play Integrity so the backend can verify requests come from the real app
[ ] Pin certificates, with backup pins and an update plan
[ ] Detect jailbroken or rooted devices for sensitive features
[ ] Use the strictest file protection classes for stored data
[ ] Prevent leaks through screenshots, the app switcher, keyboard caches, the clipboard and device logs
[ ] Validate all deep links and custom URL schemes
[ ] Make sure the backend never trusts the app, since attackers can call the API directly
11. Native and memory-unsafe code
Applies to: C, C++, unsafe Rust, or native extensions only. Skip for JavaScript, Python, Go, Java and similar apps without native modules.
[ ] Check for buffer overflows, use-after-free, integer overflows and format string bugs
[ ] Consider memory-safe languages (Rust, Go, Swift) for security-critical parts
[ ] Enable compiler hardening: stack canaries, ASLR/PIE, RELRO, control-flow integrity, FORTIFY_SOURCE
[ ] Run tests with sanitizers (ASan, UBSan)
[ ] Fuzz every parser and input handler (AFL++, libFuzzer)
[ ] Sandbox code that parses untrusted input (seccomp, privilege separation)
[ ] Review every unsafe block and FFI boundary
12. Cryptography and key management
Applies to: apps that encrypt data, sign things or generate tokens.
[ ] Use audited, well-known crypto libraries; never write your own crypto
[ ] Use cryptographically secure randomness for tokens and IDs
[ ] Compare tokens and signatures in constant time
[ ] Check for leaks through response timing, response sizes or differing error messages
[ ] Remove weak algorithms: MD5, SHA1, DES, ECB mode
[ ] Never reuse nonces or IVs
[ ] Check for padding oracle vulnerabilities
[ ] Use TLS 1.2+ (ideally 1.3) with forward secrecy
[ ] Keep master keys in a cloud KMS or HSM and use envelope encryption
[ ] Give every key an owner, purpose, rotation schedule and revocation plan
[ ] Make crypto swappable without rewriting the app (crypto agility)
[ ] High-security: plan for post-quantum crypto (NIST ML-KEM and ML-DSA)
[ ] High-security: use end-to-end encryption where the server should never see plaintext
[ ] Government / regulated: use FIPS 140-3 validated modules
13. Dependencies and supply chain
Applies to: every app with third-party packages.
[ ] Update dependencies and run the audit tool for your ecosystem (npm audit, pip-audit, cargo audit, bundler-audit)
[ ] Remove unused packages
[ ] Commit the lockfile and install from it in builds (npm ci or equivalent)
[ ] Check for typosquatted packages (misspelled copies of popular names)
[ ] Check for packages with suspicious install scripts
[ ] Flag abandoned packages and watch for maintainer takeovers
[ ] Review the actual diff of updates to critical packages, not just the version number
[ ] Check dependency licenses for legal problems
[ ] Enable Dependabot or Renovate plus secret scanning on the repo
[ ] GitHub Actions: pin actions to commit SHAs, not tags
[ ] CI/CD: make sure secrets can't leak into logs or to pull requests from forks
[ ] High-security: generate an SBOM for every release
[ ] High-security: reproducible, hermetic builds with SLSA level 3+ provenance
[ ] High-security: sign commits and artifacts (Sigstore, hardware keys) and verify signatures before deploying
[ ] High-security: vendor and review critical dependencies instead of pulling them live
14. Infrastructure, cloud and network
Applies to: apps you deploy and host. Skip items your managed platform (Vercel, Netlify, Heroku, Supabase) already handles for you.
Containers
[ ] Docker: run containers as a non-root user
[ ] Docker: keep secrets out of image layers
[ ] Docker: use minimal or distroless base images
[ ] Docker: use read-only filesystems where possible
[ ] Docker: scan images for vulnerabilities
Cloud and servers
[ ] Give every cloud IAM role least privilege
[ ] Make sure storage buckets aren't public
[ ] Close database, admin and SSH ports to the internet with firewalls or security groups
[ ] Disable every protocol and port that isn't needed
[ ] Define infrastructure as code, and review and scan it like code
[ ] Detect drift between declared config and what's actually running
[ ] Replace servers instead of patching them by hand (immutable infrastructure)
[ ] Self-managed servers: harden the OS against CIS benchmarks
Network and domain
[ ] Put DDoS protection or a CDN in front of the app
[ ] Filter egress so servers can only reach an allowlist of destinations
[ ] Segment the network so each tier only reaches what it must
[ ] Add DNSSEC and CAA records to the domain
[ ] Submit the domain to the HSTS preload list
[ ] Monitor certificate transparency logs for certificates issued for your domain
[ ] Remove dangling DNS records to prevent subdomain takeover
[ ] Turn on domain auto-renew and registrar lock
[ ] Microservices: use mutual TLS between internal services
[ ] Own IP ranges: monitor for BGP hijacks
15. Reliability and error handling
Applies to: every app; server items apply only to apps with a backend.
[ ] Add proper error handling everywhere, including unhandled promise rejections and crashes
[ ] Add timeouts to every outgoing call to external APIs
[ ] Add retries with backoff for flaky services
[ ] Show what happens when each third-party service goes down, and degrade gracefully
[ ] Check for memory leaks
[ ] Test with very large datasets and files
[ ] Handle date edge cases: leap years, DST changes, month ends
[ ] Backend: add graceful shutdown handling
16. Logging, monitoring, backups and incident response
Applies to: deployed apps.
Logging and monitoring
[ ] Log security events: failed logins, permission denials, admin actions
[ ] Make sure logs never contain passwords, tokens or personal data
[ ] Set up error monitoring (Sentry or similar)
[ ] Add uptime monitoring with alerts
[ ] Add request IDs to trace a problem through the logs
[ ] Alert on unusual activity (login spikes, error spikes)
[ ] High-security: centralize logs in a SIEM with synced clocks
[ ] High-security: make logs tamper-evident (hash chains, write-once storage)
[ ] High-security: plant honeytokens and canary credentials that alarm when touched
[ ] High-security: add runtime threat detection (Falco or similar)
Backups and recovery
[ ] Automate backups and test that they actually restore
[ ] Keep an immutable or offline backup copy that ransomware can't reach
[ ] Define recovery time and recovery point targets and verify them
[ ] Plan for losing a whole cloud account: could you rebuild elsewhere?
Incident response
[ ] Write a short runbook for what to do if you get hacked
[ ] Teams: rehearse it with tabletop exercises
[ ] High-security: prepare forensic readiness (how to capture disk and memory evidence)
17. Performance, cost, code quality and testing
Applies to: every app.
Performance
[ ] Find performance bottlenecks
[ ] Add caching where it makes sense
[ ] Frontend: optimize images and assets, reduce bundle size, lazy load heavy components
Cost and expiry
[ ] Find code that could run up a huge cloud bill (unbounded loops, serverless functions that trigger themselves)
[ ] Set billing alerts on every paid service
[ ] List everything that expires: SSL certificates, API keys, domains, free tier limits, deprecated API versions
Code quality
[ ] Find and remove dead code
[ ] Find duplicated code
[ ] Fix lint and type errors
[ ] Simplify overly complex functions
[ ] Check naming and folder structure consistency
[ ] Write a README with setup instructions
Testing
[ ] Add tests for critical paths (auth, payments, data changes)
[ ] Check test coverage
[ ] Add tests for edge cases and bad input
[ ] Add security tests that try to bypass auth and access other users' data
[ ] Run static analysis (CodeQL, Semgrep)
[ ] Web: run a dynamic scanner (OWASP ZAP) against staging
18. Privacy, legal and compliance
Applies to: apps that collect personal data or serve the public.
[ ] List what personal data you collect and store, and cut what you don't need (including metadata)
[ ] Let users delete their account and data
[ ] Let users export their data
[ ] Check whether GDPR or CCPA apply, and add cookie consent if needed
[ ] Make sure the privacy policy and terms match what the app actually does
[ ] Sign data processing agreements with vendors that handle user data
[ ] Check accessibility laws that apply to your business
[ ] Map controls against the OWASP ASVS (level 1 for most apps, 2 for sensitive data, 3 for critical systems)
[ ] Health data: HIPAA
[ ] Card payments: PCI DSS scope
[ ] B2B customers: SOC 2 and ISO 27001
[ ] High-security: process data on-device where possible, use differential privacy for analytics, and design so even you can't read users' most sensitive data
19. Accounts, people and process
Applies to: every project. These live outside the code, so you check them yourself.
[ ] Turn on 2FA for GitHub, hosting, domain registrar, payment provider and email, ideally with passkeys or hardware keys
[ ] Review who has access to the repo, hosting and database, and remove anything unused
[ ] Add branch protection so nobody can push straight to production
[ ] Encrypt every laptop with access to production
[ ] Store recovery codes and backup keys somewhere secure and separate
[ ] Teams: remove access instantly when someone leaves
[ ] Teams: require code review on every merge
[ ] Teams: train everyone on phishing with realistic tests
[ ] Teams: require two-person approval for production access and pipeline changes
[ ] Teams: use just-in-time admin access instead of standing admin rights, plus sealed break-glass accounts
[ ] Teams: log and review employee access to user data
[ ] Teams, high-security: background checks and dedicated admin workstations
20. High-security tier
Applies to: apps holding financial, health or government data, or facing well-funded attackers. Skip for typical apps; the sections above already cover them.
Zero trust
[ ] No service trusts another just because it's on the same network
[ ] Give every service its own identity and minimal permissions
[ ] Check device posture before granting access to admin tools
Hardware and isolation
[ ] Keep root keys in an HSM, created in a witnessed key ceremony and split with Shamir's Secret Sharing
[ ] Use confidential computing (AWS Nitro Enclaves, AMD SEV, Intel TDX) for the most sensitive workloads
[ ] Sandbox risky workloads in gVisor or Firecracker microVMs
[ ] Self-managed servers: secure boot, measured boot and TPM remote attestation
[ ] Self-managed servers: keep firmware and BMC/IPMI updated, on a fully isolated management network
[ ] Self-managed servers: know where the hardware physically is and who can touch it
Adversarial testing
[ ] Hire external penetration testers regularly
[ ] Run a bug bounty program
[ ] Run red team exercises, including social engineering and physical access
[ ] Fuzz continuously (OSS-Fuzz or equivalent)
[ ] Formally verify the most critical components
Government frameworks
[ ] Map controls against NIST 800-53; FedRAMP High and CMMC if you sell to the US government
