# C++

## Toolchain (use the project's CMake or build files)
- Standard from the project (`CMAKE_CXX_STANDARD`, usually C++17 to C++23). Warnings as errors: `-Wall -Wextra -Wpedantic -Wconversion -Werror` (MSVC: `/W4 /WX`).
- Build and test: `cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure`.
- Sanitizers in test builds: `-fsanitize=address,undefined`, and `-fsanitize=thread` separately for threaded code. Static analysis: `clang-tidy`, `cppcheck`. Format: `clang-format`.

## Ownership and lifetime
- RAII for every resource: memory, files, locks, sockets. No naked `new`/`delete`; use `std::make_unique` by default, `std::shared_ptr` only for genuinely shared ownership, plain references or raw pointers only as non-owning observers.
- Rule of zero: let members manage themselves. If you write one of destructor, copy or move operations, define or delete all five.
- Dangling is the main hazard: never return a reference or `std::string_view`/`std::span` to a local or a temporary; do not keep views past the owner's lifetime; do not hold iterators across container modification.
- Move semantics: pass by value and `std::move` to sink, by `const&` to read, by `&&` rarely. Do not `std::move` a `const` object or the return value of a function (it blocks copy elision).

## Idioms
- `const` and `constexpr` wherever possible. `enum class` over plain `enum`. `override` and `final` on virtuals. Virtual destructor on a polymorphic base.
- Prefer standard containers and algorithms to hand-written loops and raw arrays. `std::array`, `std::vector`, `std::string`. Reserve capacity when the size is known.
- `std::optional` for maybe-values, `std::variant` for sum types, `std::expected` (C++23) or a project result type for recoverable errors. Follow the project's choice between exceptions and error codes; do not mix styles inside one module.
- Mark `noexcept` only where true. Destructors must not throw.
- Avoid `using namespace` in headers, C-style casts and `reinterpret_cast`. Use `static_cast` with a reason. No macros where a `constexpr` or template works.
- Undefined behavior to design out: signed overflow, out-of-bounds access, use after free, data races, uninitialized reads, strict-aliasing violations. Use `.at()` or checked access in code that handles untrusted input.

## Concurrency
- `std::jthread`/`std::thread` joined on every path, `std::scoped_lock` for several mutexes, `std::atomic` with the default memory order unless you can justify a weaker one. Never hold a lock while calling unknown code.

## Build hygiene
- Modern CMake: `target_link_libraries`, `target_include_directories`, `target_compile_features` with PUBLIC/PRIVATE; no global flags. Headers self-contained and include what they use. Pin third-party dependencies (vcpkg, Conan, FetchContent with a fixed tag or hash).

## Testing
- GoogleTest or Catch2 through `ctest`. Run under sanitizers. Fuzz parsers of untrusted input.
