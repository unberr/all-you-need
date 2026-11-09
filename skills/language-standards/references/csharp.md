# C# and .NET

## Toolchain
- Check: `dotnet build -warnaserror`, `dotnet test`, `dotnet format --verify-no-changes`. SDK from `global.json`, target framework from the `.csproj`.
- Project settings to expect and keep: `<Nullable>enable</Nullable>`, `<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`, analyzers on (`<AnalysisMode>`, `.editorconfig`).
- Dependencies: `dotnet list package --vulnerable --include-transitive` for advisories, central versions via `Directory.Packages.props` where used.

## Idioms that prevent defects
- Nullable reference types on: no `!` suppression to silence a warning; fix the flow. Use `required` members, records for immutable data, pattern matching and `switch` expressions for branching.
- Async: `async Task` / `async Task<T>`, never `async void` except event handlers. Never block with `.Result`, `.Wait()` or `.GetAwaiter().GetResult()` on async work. Pass `CancellationToken` through every async call chain. Use `ConfigureAwait(false)` in library code. Do not fire and forget; await or track every task.
- Dispose what you own: `using` / `await using` for `IDisposable` and `IAsyncDisposable`. One `HttpClient` through `IHttpClientFactory`, not `new HttpClient()` per request.
- Exceptions: catch the specific type, rethrow with `throw;` (not `throw ex;`), do not use exceptions for expected control flow, never swallow with an empty `catch`.
- `decimal` for money, `DateTimeOffset` for instants (store UTC), `StringComparison.Ordinal` or `OrdinalIgnoreCase` for non-linguistic comparisons, `Guid`/typed ids for identity.
- LINQ is lazy: materialize once with `ToList()` when enumerating more than once. Avoid multiple enumeration and capturing loop state in deferred queries.
- Logging: structured message templates with `ILogger` (`_logger.LogInformation("Order {OrderId} shipped", id)`), never string interpolation, and no secrets or personal data.

## ASP.NET Core and EF Core
- Dependency injection through constructors; match lifetimes (a singleton must not capture a scoped service). Options pattern for configuration, validated at startup.
- Validate input with data annotations or FluentValidation; return `ProblemDetails`. Authorize with policies and `[Authorize]`; deny by default. Use anti-forgery tokens for cookie-authenticated form posts; configure CORS with explicit origins.
- Secrets: user-secrets in development, environment or a vault in production. Never in `appsettings.json` committed to source.
- EF Core: parameterized by default (do not concatenate into `FromSqlRaw`; use `FromSqlInterpolated`). Prevent N+1 with `Include` or projection to DTOs, use `AsNoTracking()` for read-only queries, paginate, keep migrations reviewed and reversible.
- Do not use `BinaryFormatter` or other unsafe deserializers on untrusted data (it is removed from modern .NET).

## Testing
- xUnit or NUnit with `dotnet test`. Test through public APIs; use `WebApplicationFactory` for HTTP integration tests; fake time with `TimeProvider`. No real network or shared database state between tests.
