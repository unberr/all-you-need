# Input and output handling

Treat everything that crosses a trust boundary as hostile: request bodies, query strings, headers, cookies, file names and contents, webhook payloads, third-party API responses, database content written by others, environment from untrusted sources, and model output.

## Validate at the boundary
- Check type, length, format, range, encoding and business rules with an allowlist of what is valid, not a denylist of what is bad. Reject, do not silently repair. Validate on the server even when the client validates too.
- Parse into typed values immediately (schema libraries: pydantic, zod, FluentValidation, Bean Validation, serde). After that, code works with validated types.
- Constrain sizes everywhere: body, string length, array length, nesting depth, upload size, number of fields.

## Injection: never build code from strings
- **SQL and NoSQL:** parameterized queries or the ORM's bound parameters. Allowlist identifiers (column or table names, sort fields) because they cannot be parameterized. For NoSQL reject operator objects in user input (`$ne`, `$gt`, `$where`) by validating types.
- **OS commands:** avoid shells. Call the program with an argument list; if a shell is unavoidable, allowlist the input and quote with the language's escaping function. Never pass user input as an option name; use `--` before untrusted arguments.
- **Other interpreters:** LDAP, XPath, XML, template engines (server-side template injection), `eval`, expression languages, regex built from input (ReDoS: bound input length, use linear-time engines), header and email injection (strip CR and LF).
- **XML:** disable external entities and DTDs (XXE). **YAML:** safe loaders only.

## Output encoding by context
- HTML body, attribute, JavaScript, CSS, URL and JSON each need different encoding. Use the template engine's auto-escaping and keep it on. Never insert untrusted input into `<script>`, event handlers or `style` unencoded.
- Rendering HTML from users (rich text): a maintained sanitizer with an allowlist (DOMPurify, Bleach, HtmlSanitizer), then a CSP as a second layer.
- Set correct `Content-Type` and `X-Content-Type-Options: nosniff`. Return JSON with a JSON content type.

## SSRF
- Do not fetch user-supplied URLs unless needed. When you must: allowlist schemes (https) and hosts; resolve DNS yourself, then connect to the checked IP (prevents DNS rebinding); block loopback, link-local (`169.254.169.254` cloud metadata), private ranges (10/8, 172.16/12, 192.168/16), IPv6 equivalents and non-HTTP ports; do not follow redirects blindly (re-validate each hop); cap size and time; use an egress proxy or network policy; on cloud, require IMDSv2.

## Path traversal and files
- Never join user input into a path directly. Resolve to a canonical absolute path and verify it stays under the allowed base directory (`Path.resolve()` plus `is_relative_to`, `filepath.IsLocal`, `Path.GetFullPath` plus prefix check). Reject `..`, absolute paths, null bytes and symlinks that escape. Prefer ids that map to stored names over user-supplied file names.
- **Uploads:** limit size and count; allowlist extensions and verify the real type from content (magic bytes), ignore the client's `Content-Type` and name; generate a random stored name; store outside the web root or in object storage with no execute permission; serve with `Content-Disposition: attachment` and a safe content type from a separate domain when possible; scan for malware where the risk justifies it; strip metadata from images; reject archives that expand beyond limits (zip bombs) and entries with `..` (zip slip).

## Deserialization
- Never deserialize untrusted data into arbitrary objects (`pickle`, `marshal`, Java `ObjectInputStream`, .NET `BinaryFormatter`, PHP `unserialize`, Ruby `Marshal`, YAML object tags). Use data-only formats (JSON) validated against a schema, and map to known types explicitly.

## Redirects and URLs
- Open redirects: redirect only to relative paths or allowlisted hosts. Validate URL schemes; reject `javascript:` and `data:`.

## LLM input and output
- Prompts, retrieved documents, repository files, web pages, tool results and model output are untrusted. Do not execute model output as code, SQL or shell without validation and a human or sandbox boundary. Do not let model output choose a privileged action. Strip or flag instruction-like text in retrieved content. See `ai-guardrails.md`.
