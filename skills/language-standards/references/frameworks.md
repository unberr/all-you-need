# Framework pitfalls (check the installed version first)

Read the project's framework version and docs before applying anything here. These are the recurring defects.

## Python
- **Django:** `DEBUG=False`, `ALLOWED_HOSTS`, `SECRET_KEY` from the environment, CSRF middleware on; `select_related` and `prefetch_related` to avoid N+1; `get_object_or_404` scoped to the user's queryset (IDOR); migrations reviewed and reversible; never `mark_safe` on user input; validate with forms or serializers; `transaction.atomic` for multi-step writes; Celery tasks idempotent.
- **FastAPI:** typed pydantic models for requests and responses (`response_model` so internals do not leak); dependency injection for auth and database sessions; `async def` only with async I/O (blocking calls in async routes stall the loop); explicit CORS origins; background tasks are not durable.
- **Flask:** application factory, `SECRET_KEY` from the environment, `debug=False` in production, validate input with a schema library, CSRF protection (Flask-WTF) for cookie sessions.

## JavaScript and TypeScript
- **Express:** `helmet`, rate limiting, body size limits, centralized error middleware that does not leak internals, async handlers that forward errors (Express 5 does it natively; earlier versions need a wrapper), validate with a schema before use, no `trust proxy` without a reason.
- **NestJS:** DTOs with `class-validator` and `ValidationPipe` (`whitelist: true`, `forbidNonWhitelisted`), guards for authorization on every controller, no business logic in controllers, injectable services with request scope only when needed.
- **Next.js:** know which code runs on the server and which in the browser; only `NEXT_PUBLIC_*` reaches the client; authorize in server actions and route handlers, not in client components; do not trust middleware alone for authorization; cache and revalidation set deliberately; `dangerouslySetInnerHTML` only with sanitized input.
- **React:** see `javascript.md`; keys, effect dependencies, derived state, cleanup. **Vue:** `v-html` only with sanitized input, `computed` for derived state, cleanup in `onUnmounted`. **Angular:** do not bypass `DomSanitizer` casually, unsubscribe or use `takeUntilDestroyed`, `OnPush` for large trees.

## Java and Kotlin
- **Spring Boot:** constructor injection, `@Valid` request bodies, method security (`@PreAuthorize`), actuator endpoints restricted, no `ddl-auto: update` in production, `@Transactional` at the service layer with the right propagation, avoid N+1 with fetch joins or entity graphs, externalized configuration and secrets.

## PHP
- **Laravel:** `$fillable` against mass assignment, Form Requests for validation, policies and gates for authorization, `APP_DEBUG=false` and `APP_KEY` secret in production, `with()` for eager loading, queued jobs idempotent, `php artisan config:cache` only after env is final. **Symfony:** validator constraints, Security component voters, parameters from environment, Doctrine queries parameterized.

## C#
- **ASP.NET Core:** see `csharp.md`; `[Authorize]` with policies, anti-forgery for cookie auth, options pattern with validation on start, `IHttpClientFactory`, EF Core `AsNoTracking` for reads and no raw SQL concatenation.

## Ruby
- **Rails:** strong parameters, `includes` for N+1, `protect_from_forgery`, parameterized `where`, no `html_safe` on user input, reversible migrations with `strong_migrations`-style safety, credentials not in the repo.

## Go
- `net/http` servers with timeouts, `context` through handlers, `database/sql` placeholders, structured logging with `slog`, graceful shutdown with `Server.Shutdown`. Router choice (chi, gin, echo) follows the project; middleware order matters (recover, request id, logging, auth).

## Rust
- **Axum, Actix:** typed extractors for validation, shared state behind `Arc` with the right lock, no blocking calls in handlers, tower layers for timeouts and rate limits, error type implementing `IntoResponse` that hides internals.
