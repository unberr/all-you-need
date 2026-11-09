---
name: performance-reliability
description: Performance, scalability, concurrency, resource and memory safety, database and network efficiency, cross-platform and container compatibility. Use for loops over data, queries, I/O, concurrency, manual memory, or multi-OS targets.
---

# performance-reliability

Measure before optimizing, but never write the obvious inefficiency in the first place. Correctness first, then the hot path.

## Algorithms and data structures
- State the complexity of anything that runs over user-sized data. Watch for accidental O(n^2): a lookup inside a loop (`list.contains`, `in list`, `indexOf`, nested loops over the same data), string concatenation in a loop, repeated sorting, repeated parsing, `.filter` inside `.map`.
- Use a set or map for membership and lookups, a heap or sorted structure for ordered access, a deque for queues, a builder for strings, a generator or stream for data too big for memory.
- Do work once: hoist invariants out of loops, cache a computed result with a clear invalidation rule, batch small operations.
- Do not micro-optimize cold code. For hot code, profile first (language profiler, flame graph, `EXPLAIN`), change one thing, measure again, and report the numbers.

## Database and ORM
- No N+1: if a loop issues one query per item, replace it with a join, an `IN` query, or eager loading (`Include`, `select_related`/`prefetch_related`, `with()`, `joinedload`, a DataLoader).
- Select only the columns and rows needed; paginate every list (keyset pagination for large tables); put limits on user-controlled queries.
- Index the columns used in `WHERE`, `JOIN` and `ORDER BY`; check the plan with `EXPLAIN`. Do not index everything: writes pay for every index.
- Use transactions for multi-step changes and keep them short. Use parameterized queries. Set connection pool sizes and query timeouts.
- Migrations: backward compatible with the running code (add column nullable or with a default, backfill, then enforce, then drop in a later release); avoid long table locks (create indexes concurrently where supported); every migration reversible or explicitly marked one-way; test it against production-sized data when risky.

## Concurrency safety
- Name the shared mutable state and what protects it. Prefer immutability, message passing and confinement to one thread or task over locks.
- Locks: acquire in a consistent global order to prevent deadlock, hold them briefly, never call unknown code or block on I/O while holding one. Check-then-act on shared data is a race unless done atomically or under one lock.
- Async code: never block the event loop with CPU work or synchronous I/O; always await or track tasks; bound concurrency (semaphore, worker pool); propagate cancellation and timeouts.
- Idempotency: retried or duplicated requests, jobs and messages must not double-apply. Use idempotency keys or unique constraints.
- Run the language's race detector or sanitizer (`go test -race`, ThreadSanitizer) on concurrent code.

## Resource safety
- Every file, socket, connection, lock, transaction, temp file and thread you open is released on every path including errors: `with`, `using`, `defer`, `try/finally`, RAII, `AutoCloseable`.
- Bound everything that can grow: queues, caches (size and TTL), in-memory buffers, request bodies, retry counts, log volume. Add backpressure instead of unbounded buffering.

## Memory (C, C++, Rust unsafe, and long-running processes)
- One owner per allocation, freed once on every path. No use after free, double free, buffer overflow or uninitialized read. Run AddressSanitizer, UBSan and Valgrind or Miri; use RAII or ownership types.
- In garbage-collected languages, leaks are references that never die: listeners, timers, caches, global maps, closures. Remove what you add.
- Avoid needless copies and allocations in hot paths: reuse buffers, pass references or views, reserve capacity, stream instead of loading whole files.

## Network and payload efficiency
- Fewer, smaller requests: batch calls, avoid chatty round trips, avoid N+1 over HTTP, use pagination and field selection.
- Compress responses (gzip or brotli), send only the needed fields, use conditional requests (`ETag`, `If-None-Match`) and cache headers, use HTTP keep-alive and connection reuse.
- Timeouts and bounded retries with exponential backoff and jitter on every outbound call; a circuit breaker for flaky dependencies. Stream large payloads.
- Frontend: ship less JavaScript, lazy-load, serve modern image formats at the displayed size.

## Scalability readiness
- Keep services stateless: session and cache state in a shared store, not process memory. Make work horizontally scalable and idempotent. Move slow work to a queue. Add caching with a defined invalidation rule. Rate-limit and paginate. Index what you query. Do not pre-build distributed infrastructure the problem does not need; make sure nothing blocks it later.

## Cross-platform and container compatibility
- Paths: use the language's path API (`pathlib`, `path.join`, `filepath.Join`, `Path::join`), never hardcoded separators. Remember Windows is case-insensitive, Linux is case-sensitive, and path length and reserved names differ.
- Line endings: do not depend on `\n` versus `\r\n`; open text files with an explicit encoding (UTF-8). Do not assume a shell: avoid shell-specific commands in code, call programs with argument lists.
- Do not assume a case-sensitive file system, `/tmp`, a home directory, a locale, a timezone (use UTC), a CPU architecture or endianness, a TTY, or specific binaries on `PATH`.
- Containers: read configuration from environment variables, log to stdout and stderr, handle `SIGTERM` for graceful shutdown, run as a non-root user, respect memory and CPU limits, do not write to the image file system. Pin base images and dependencies.
- Test on the targets that matter (CI matrix for the operating systems and runtime versions you claim to support).
