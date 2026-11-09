# Rust

## Toolchain
- Check in this order: `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings`, `cargo test --all-features`. Doc tests run with `cargo test`. Edition and MSRV from `Cargo.toml`.
- Dependencies: `cargo audit` (RustSec advisories) and `cargo deny check` (licenses, bans, advisories) when installed. Commit `Cargo.lock` for binaries.

## Errors
- Return `Result`; propagate with `?`. Libraries expose typed errors (`thiserror`); applications may use `anyhow` with context (`.context("...")`).
- No `unwrap()`/`expect()` in non-test code unless the invariant is proven and the `expect` message states it. No `panic!` for expected failures. Index slices with `.get()` when the index is untrusted.
- Integer arithmetic on untrusted values uses `checked_*`, `saturating_*` or `wrapping_*` deliberately; release builds wrap silently on overflow.

## Ownership and API design
- Borrow rather than clone. Take `&str`, `&[T]`, `&Path` in parameters, not `&String`, `&Vec<T>`. Return owned values when the caller needs them. Use `Cow` when a function sometimes allocates.
- Make invalid states unrepresentable: enums for variants, newtypes for units and ids, builders for many-argument constructors. Mark results that must be used with `#[must_use]`.
- Derive `Debug`, and `Clone`, `PartialEq`, `Eq`, `Hash`, `Default` only when they are correct. Keep public API small; `pub(crate)` by default.
- Iterators over index loops. Avoid `Rc<RefCell<T>>` and `Arc<Mutex<T>>` unless shared mutable state is the actual requirement.

## unsafe
- Only when necessary, in the smallest block, with a `// SAFETY:` comment stating why every precondition holds, wrapped in a safe API. Run tests under Miri (`cargo +nightly miri test`) for unsafe code.

## Async and concurrency
- Do not block the executor: use `spawn_blocking` for CPU-heavy or blocking work. Never hold a `std::sync` lock or a `MutexGuard` across `.await`. Know which futures are cancel-safe before using them in `select!`.
- Channels and ownership over shared locks. Types crossing threads are `Send`, shared ones `Sync`; let the compiler enforce it, do not wrap with `unsafe impl`.
- Bound queues and concurrency; set timeouts on network calls.

## Security
- Parse untrusted input with `serde` into typed structs (`#[serde(deny_unknown_fields)]` where strictness matters). Use parameterized queries (`sqlx`, `diesel`). Use `std::process::Command` with `.arg()`, not a shell string. Secrets from environment, wrapped in a type that does not print them.

## Testing
- Unit tests in `#[cfg(test)]` modules, integration tests in `tests/`, `proptest` for properties, `cargo fuzz` for parsers.
