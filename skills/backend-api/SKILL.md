---
name: backend-api
description: Backend engineering: layering, config, REST conventions, versioning, validation, pagination, idempotency, timeouts, transactions, migrations, pooling, data lifecycle. Use when building or changing a server, API endpoint or database access.
paths:
  - "**/routes/**"
  - "**/routers/**"
  - "**/controllers/**"
  - "**/api/**"
  - "**/migrations/**"
  - "**/schema.prisma"
  - "**/openapi.yaml"
  - "**/openapi.json"
---

# backend-api

Follow the project's existing stack and layout first. These rules fill in what it does not already decide.

## Architecture
- Structure to the size of the project: a small service can be handlers plus a service module plus data access; a larger one adds domain and infrastructure layers (see `code-structure`). Handlers parse and validate input, call a service, and map the result. Business rules live in services or the domain, not in controllers or route handlers.
- Keep I/O, business rules, authorization, serialization and presentation separate so each can be tested alone.
- Use dependency injection when it makes testing and swapping real (database, clock, mail, payment client). Do not add a container for a handful of objects.
- Prefer stateless services: sessions, caches and uploads in shared stores, not process memory, so instances can be added.
- Centralize configuration: read once at startup into a typed, validated object; fail fast on a missing or invalid variable. Keep dev, test, staging and production separate, each with its own credentials and data. No production values in the repository.
- Manage resources explicitly: connection pools sized and bounded, files and sockets closed on every path, background jobs with timeouts and cancellation, graceful shutdown on `SIGTERM`.

## API design
- Resources as nouns, standard methods: `GET` read (safe, no side effects), `POST` create or action, `PUT` replace, `PATCH` partial update, `DELETE` remove. Plural collection names, stable ids.
- Consistent response and error envelope across the API: the same shape for success, validation errors (field-level) and failures, with a machine-readable code and a correlation id. Correct status codes: 200, 201 with `Location`, 204, 400 or 422, 401, 403, 404, 409 conflict, 429, 5xx for server faults only.
- Validate every request on the server against an explicit schema (types, ranges, lengths, enums, required fields), and shape every response from an explicit schema so internal fields never leak. Reject unknown or malformed input with a clear 4xx.
- **Pagination** on every list endpoint: keyset (cursor) for large or changing data, offset for small; enforce a maximum page size; return paging metadata.
- **Filtering and sorting** through allowlisted fields and operators with validated values; never pass raw user text into a query or `ORDER BY`.
- **Limits:** maximum request body size, maximum nesting depth, upload limits. **Timeouts:** server request timeout, and timeouts and bounded retries on every outbound call and database query.
- **Idempotency:** `GET`, `PUT` and `DELETE` are idempotent by design. For `POST` that creates money-affecting or externally visible effects, accept an idempotency key and store the result so a retry returns the same outcome. Message and job handlers must tolerate redelivery.
- **Versioning:** version the API (path or header) from the start; changes to existing versions are additive. Breaking changes ship as a new version with a deprecation path and date. Do not change existing response shapes, field meanings or status codes silently.
- **Documentation:** keep an OpenAPI (or equivalent) schema that is the contract, generated from or validated against the code, with examples; update it in the same change as the endpoint.

## Database and data
- **Efficient queries:** select only needed columns and rows, no query inside a loop (fix N+1 with joins, `IN`, eager loading or batching), index the columns used in filters, joins and ordering based on the real query patterns, check plans with `EXPLAIN`.
- **Transactions:** wrap multi-step changes that must succeed or fail together; keep them short; no network calls inside a transaction; pick the isolation level on purpose; retry on serialization failures.
- **Concurrency:** prevent lost updates with optimistic locking (version column), `SELECT ... FOR UPDATE`, atomic updates (`UPDATE ... SET n = n + 1`) or unique constraints; never check-then-insert without a constraint.
- **Integrity:** enforce rules in the database too: primary and foreign keys, `NOT NULL`, `UNIQUE`, `CHECK`, appropriate types (decimal for money, timestamptz in UTC).
- **Migrations:** versioned, reviewed, reproducible, applied by the pipeline. Backward compatible with the running code: add nullable or defaulted columns, backfill, then enforce, then remove old columns in a later release. Avoid long locks (create indexes concurrently where supported, batch backfills). Reversible or explicitly one-way with a recovery plan. Back up before destructive changes.
- **Connection pooling:** one pool per process with sensible min and max, timeouts for acquiring and for queries, connection validation, and the pool limit multiplied by instance count kept under the database's connection limit.
- **Data lifecycle:** define retention, soft versus hard delete, archival and cleanup jobs for each kind of data; honor deletion requests across copies, caches and backups; log what was deleted without logging the data.

## Observability hooks the backend owns
Structured logs with a correlation id, metrics (rate, errors, latency), health (liveness) and readiness endpoints that reveal nothing internal, and clear error logging at the boundary where the exception is handled.
