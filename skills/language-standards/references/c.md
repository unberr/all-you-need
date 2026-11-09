# C

## Toolchain (use the project's build system: Make, CMake, Meson)
- Compile with warnings as errors: `-std=c17 -Wall -Wextra -Wpedantic -Werror` (plus `-Wconversion -Wshadow` where the code allows). Use the project's declared standard.
- Run tests under sanitizers: `-fsanitize=address,undefined -fno-omit-frame-pointer -g`. Use `-fsanitize=thread` separately for threaded code. `valgrind` where sanitizers are unavailable.
- Static analysis: `clang-tidy`, `cppcheck`. Format: `clang-format` with the project's config.

## Memory and bounds (the source of most C vulnerabilities)
- Check every `malloc`, `calloc`, `realloc`, `fopen` return. `realloc` into a temporary pointer so the original is not lost on failure.
- Every allocation has exactly one owner and one `free` on every path, including error paths. Set freed pointers to `NULL` when they stay in scope. Prefer a single cleanup block (`goto cleanup`) for functions that acquire several resources.
- Check size arithmetic before allocating or indexing: `n * size` can overflow `size_t`; check `n > SIZE_MAX / size`. Signed overflow is undefined behavior.
- Pass a buffer and its length together. Use `snprintf` and check its return value; `memcpy`/`memmove` with verified sizes; `strnlen` for untrusted strings.
- Never use `gets`, `strcpy`, `strcat`, `sprintf` or `scanf("%s")` without a width. Never pass untrusted input as a format string: `printf("%s", s)`, not `printf(s)`.
- Initialize every variable. Do not read uninitialized memory or padding bytes (zero structs with `= {0}` or `memset` before serializing).
- Do not cast the result of `malloc`. Write `p = malloc(n * sizeof *p)`. Avoid VLAs.

## Design
- `const` for read-only parameters, `static` for file-local functions and data, include guards or `#pragma once` in headers. Headers declare, `.c` files define. Do not define variables in headers.
- Return an error code or `bool` and pass results through out-parameters, with a documented ownership rule for each pointer. Check `errno` immediately after the failing call.
- Check the return value of `close`, `fclose`, `write` and `read`; handle short reads and writes in a loop.
- Be exact with integer types: `size_t` for sizes and indexes, fixed-width types (`uint32_t`) for binary formats, explicit byte order when reading or writing files and sockets.
- Concurrency: protect shared data with a mutex or atomics; never assume `volatile` gives thread safety.

## Testing
- Unit test with a small framework (Unity, cmocka, Check) or plain `assert` programs run by the build. Run the whole suite under ASan and UBSan. Fuzz parsers (`libFuzzer`, AFL++) for anything reading untrusted input.
