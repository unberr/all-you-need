---
name: code-structure
description: How to organize code: layers, module boundaries, dependency direction, file and function size, naming, error handling strategy, configuration, project layout for backend, frontend and monorepos. Use when creating a project, adding a module, splitting a large file, or reviewing architecture.
---

# code-structure

First rule: match the structure the project already has. Introduce a new structure only when the existing one cannot hold the change, and say why.

## Boundaries and dependencies
- Dependencies point inward: domain logic knows nothing about HTTP, databases, frameworks or the UI. Frameworks and I/O sit at the edges and call into the core.
- Keep a pure core and push side effects (network, disk, clock, randomness) to the edges. Pass them in, so the core can be tested without them.
- A module has one reason to change. If describing it needs "and", split it.
- No import cycles. If two modules need each other, the shared concept is a third module.
- Public surface small, internals private. Export only what other modules use.

## Backend layering
- Transport (routes, handlers, CLI) -> application/service (use cases) -> domain (rules, types) -> infrastructure (database, queues, HTTP clients, behind interfaces the inner layers own).
- Handlers parse and validate input, call one service, map the result to a response. No business rules and no SQL in handlers.
- Separate the transport shape (request/response DTOs) from the domain model and the storage model. Map at the boundary.
- One error strategy per codebase (see `error-handling`): typed errors inside, mapped at the edge. Never leak internals, stack traces or SQL to clients.
- Configuration is read once at startup into a typed object and passed down. No scattered environment reads.
- Every outbound call has a timeout. Every list endpoint is paginated. Every migration is reversible or explicitly one-way.

## Frontend layout
- Organize by feature, not by file type: a feature folder holds its components, hooks, state, API calls and tests.
- Shared UI primitives in one place, with no knowledge of any feature. Features may import primitives, never each other's internals.
- Server state (fetched data) and client state (UI state) are different things: use a data-fetching layer with caching for the first, local state for the second. Do not copy server data into global state.
- Components stay presentational where possible: props in, events out. Data fetching and side effects live in hooks or containers.
- Derive values instead of storing them. One source of truth per fact.

## Patterns and scale
- Use a design pattern only when the problem in front of you has the shape it solves (a real second implementation, a real variation point, a real need to decouple). No factory for one product, no interface with one implementation, no event bus for two components.
- Start with functions and plain data. Add a class, an interface or a layer when the code shows you need it. Say in a sentence what trade-off you made.
- Build for the growth you can name, not for imaginary scale. Make sure nothing you write blocks that growth: keep services stateless, paginate lists, index queried columns, move slow work to a queue, keep configuration external, and avoid global mutable state. Do not pre-build distributed infrastructure.

## Size and naming
- Functions do one thing at one level of abstraction. A function that needs a long comment to follow wants to be split. As a guide: past about 40 lines or 4 levels of nesting, look for a split.
- Files around a few hundred lines or more than one major concept: look for a split. Do not split by line count alone.
- Names say what a thing is or does in the domain's words. No `utils`, `helpers`, `manager`, `data`, `info` as a dumping ground; name the module after its purpose.
- Booleans read as a question (`isReady`, `hasAccess`). Functions are verbs, types are nouns. Follow the language's casing convention.
- Prefer composition over inheritance. Prefer plain data and functions over class hierarchies unless the language or framework is built around them.

## Tests mirror the structure
- Many fast unit tests of the pure core, fewer integration tests across a boundary (database, HTTP), a handful of end-to-end tests of critical paths.
- Test files sit next to the code or in a parallel tree, following the project's convention.
- A bug gets a regression test at the lowest layer that reproduces it.

## Smells that mean restructure
Shotgun change (one idea touches ten files), god module everything imports, a function with many boolean flags, copy-pasted blocks with small differences, a layer that skips another, a "common" package that only grows.

## Layout starting points (use only when starting from nothing)
- Python service: `src/<pkg>/{api,services,domain,infra}`, `tests/`, `pyproject.toml`.
- Node/TypeScript service: `src/{routes,services,domain,infra}`, `test/`, `tsconfig.json`.
- Go: `cmd/<app>/main.go`, `internal/<domain>/...`, `pkg/` only for code meant to be imported by others.
- Rust: a `lib.rs` core with thin `main.rs`; workspace crates split along real boundaries.
- C#: solution with `Domain`, `Application`, `Infrastructure`, `Web` projects, dependencies pointing inward.
- PHP: PSR-4 autoloaded `src/`, framework conventions for controllers, separate `Service` and `Repository` classes.
- C and C++: `include/<project>/` public headers, `src/` implementation, `tests/`, built by one build system (CMake or the project's own).
