# Threat modeling and secure design

Do this before writing code for anything that handles authentication, authorization, money, personal data, file uploads, outbound requests, integrations, or new public endpoints. Keep it short: a few lines in the plan, or a table in the report.

## Steps
1. **Assets:** what is worth stealing or breaking (credentials, personal data, money, availability, integrity of records, the host machine, the build pipeline).
2. **Trust boundaries:** where data crosses from less trusted to more trusted (browser to server, server to database, service to service, third-party webhook, file upload, model output, repository content). Every crossing needs validation, authentication and authorization.
3. **Attackers:** anonymous internet user, authenticated user attacking another user, malicious tenant, compromised dependency, insider, compromised internal service.
4. **Abuse cases:** for each entry point ask what a hostile caller does with it. Use STRIDE as a prompt: Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of privilege.
5. **Attack surface:** list endpoints, parameters, file inputs, background jobs, admin tools, debug routes, third-party scripts, open ports, secrets. Remove what is not needed.
6. **Mitigations and residual risk:** one control per threat, plus what remains. Record assumptions.

## Design principles that follow
- **Secure by default:** TLS on, authentication required, deny-by-default authorization, secure cookie flags, restrictive file permissions, closed CORS, no debug features.
- **Least privilege:** the minimum permissions for users, services, containers, database accounts, cloud roles and API tokens. Separate read and write credentials.
- **Defense in depth:** never one control. Combine validation, authorization, encryption, rate limiting, monitoring and safe defaults, so one failure is not a breach.
- **Fail securely:** on error deny access, close resources, return a generic message, never fall back to a permissive path.
- **No security through obscurity:** hidden URLs, obfuscation, client-side checks and undocumented APIs are not controls. Assume the attacker has the client code and the API list.
- **Separation of duties:** authentication, authorization, audit logging, secret management and business logic are separate components, so a bug in one does not disable the others.
- **Vetted primitives:** reuse established libraries and framework features for authentication, sessions, authorization, cryptography, rate limiting and validation. Do not hand-roll them. Use the project's approved shared security services when they exist.

## Report format
`Threats considered: ... | Controls: ... | Residual risk: ... | Needs human review: ...`
