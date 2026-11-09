---
name: error-handling
description: Error handling strategy: what to handle, where, how to surface it per language, typed errors, boundaries, retries and user-facing messages. Use when writing code that can fail, designing an error model, or reviewing catch blocks.
---

# error-handling

## Principles
- Handle errors that can actually occur, at the boundary where they occur and where you can act on them. Do not wrap internal calls in a catch-all, null-check a value the type system says is non-null, or add fallbacks for unreachable states; that hides real bugs and implies failure modes that do not exist.
- At real boundaries (user input, requests, files, environment, external services, rows whose schema you do not control) be strict and specific about what is wrong.
- Never swallow an error. An empty catch, bare `except:`, discarded error value and `unwrap` on a fallible production call are the same defect in different syntax.
- Catch the specific failure, not the base class. Keep the cause: `raise X from err`, `fmt.Errorf("...: %w", err)`, `Error.cause`, `anyhow` context.
- Fail closed: an error in an authorization or validation step denies, never allows.

## Per language idiom
- Python: narrow `except`, custom exception classes for domain errors, `raise ... from`, context managers for cleanup.
- TypeScript and JavaScript: `throw` Error subclasses, typed `catch (err: unknown)` with narrowing, reject promises with Errors, never throw strings, handle every promise.
- Go: return `error` last, check every one, wrap with `%w`, `errors.Is` and `errors.As`, sentinel errors for conditions callers branch on.
- Rust: `Result` with `?`, `thiserror` for libraries, `anyhow` for applications, no `unwrap` in production paths.
- C#: specific catch types, `throw;` to rethrow, no exceptions for expected control flow.
- C: check every return value and `errno`, single cleanup path.

## Surfaces
- Inside the system: typed errors with context for logs. At the edge: mapped to protocol errors (status codes, exit codes) with a safe message and a correlation id; no stack traces, SQL, paths or internals to users.
- Log once, at the layer that handles it; do not log and rethrow at every level.
- Retries only for known transient failures, bounded, with backoff and jitter, on idempotent operations. A retry added to hide an unexplained failure is a bug.
- A function either handles an error or returns it; it does not return a misleading success value.
