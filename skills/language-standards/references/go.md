# Go

## Toolchain
- Check: `gofmt -l .` (must print nothing), `go vet ./...`, `go test -race ./...`. Also `staticcheck ./...` or `golangci-lint run` when configured, and `govulncheck ./...` for known vulnerabilities. Go version from `go.mod`.
- `go mod tidy` after dependency changes; commit `go.sum`.

## Errors
- Return `error` as the last value and check every one. Wrap with context using `fmt.Errorf("load config: %w", err)`; compare with `errors.Is` and `errors.As`. Errors are values: no `panic` for expected failures, and no string matching on messages.
- Do not both log and return an error; do one, at the right layer. Sentinel errors for conditions callers branch on.

## Concurrency
- Every goroutine has an owner, a way to stop (cancel a `context.Context` or close a channel) and a way to be waited on (`sync.WaitGroup` or `errgroup`). No goroutine without a defined exit: that is a leak.
- The sender closes a channel, never the receiver. Do not send on a closed channel. Know whether a channel is buffered and why.
- Protect shared state with `sync.Mutex` or `sync/atomic`, or confine it to one goroutine. `go test -race` must pass. Before Go 1.22 loop variables are shared across iterations: copy them before capturing in a goroutine (Go 1.22+ gives each iteration its own).
- `context.Context` is the first parameter, is never stored in a struct, and is passed to everything that can block. Set deadlines.

## Idioms
- Accept interfaces, return concrete types; define small interfaces where they are used. Make the zero value useful. Avoid `init()` and package-level mutable state.
- `defer` right after acquiring a resource (`defer f.Close()`, `defer mu.Unlock()`). `defer` in a long loop runs at function end: wrap the body in a function.
- Slices share backing arrays: `append` may or may not copy, so copy explicitly when you need independence. Pre-size with `make([]T, 0, n)` when the size is known. Nil maps panic on write.
- `time.Duration` for durations, `time.Time` for instants (compare with `Equal`). `strings.Builder` for building strings. Structured logging with `log/slog`.

## Security
- `crypto/rand`, not `math/rand`, for tokens and keys. `database/sql` with placeholders (`?`/`$1`), always `defer rows.Close()` and check `rows.Err()`. `html/template` for HTML, never `text/template`.
- `http.Client` and `http.Server` with timeouts set (`Client.Timeout`, `ReadHeaderTimeout`, `ReadTimeout`, `WriteTimeout`); `http.MaxBytesReader` for request bodies. Never set `InsecureSkipVerify: true`. Run subprocesses with `exec.Command(name, args...)`, not `sh -c` with input.
- Clean paths with `filepath.Clean` and verify they stay inside the base directory (`os.Root` in Go 1.24+, or `filepath.IsLocal`).

## Testing and layout
- Table-driven tests with `t.Run`, `t.Helper()` in helpers, `t.Parallel()` where safe, `testing/fstest` and `httptest` instead of real files and servers. Fuzz tests (`go test -fuzz`) for parsers.
- Layout: `cmd/<app>/main.go`, code in `internal/`, packages named for what they provide (no `util`, `common`).
