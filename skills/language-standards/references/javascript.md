# JavaScript (Node.js and browser, including React)

## Toolchain (use what package.json declares)
- Node version from `.nvmrc` or `engines`. Package manager from the lockfile (`package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb`). Install with the lockfile in CI (`npm ci`).
- Lint: `eslint` (or `biome`). Format: `prettier` (or `biome`). Tests: `vitest` or `jest`, or the built-in `node --test`. Audit: `npm audit`.
- ES modules or CommonJS: follow `"type"` in package.json. Do not mix.

## Idioms that prevent defects
- `const` by default, `let` when reassigned, never `var`. Strict equality `===`. Optional chaining `?.` and nullish `??` (not `||`, which also catches `0` and `""`).
- Every promise is awaited, returned, or deliberately handled. No floating promises. `async` inside `forEach` does not wait: use `for...of` or `Promise.all`.
- `Promise.all` fails fast; use `Promise.allSettled` when you need every result. Handle rejections; set timeouts with `AbortController` / `AbortSignal.timeout`.
- Do not mutate arguments or shared objects; copy with spread or `structuredClone`.
- Numbers are IEEE doubles: use integer minor units or a decimal library for money, `BigInt` beyond 2^53.
- Dates: store ISO 8601 UTC strings or timestamps; use `Intl` for display.
- Clean up what you start: remove event listeners, clear timers, close streams and database handles.
- Node: no synchronous file or crypto calls in request paths; respect stream backpressure; handle `unhandledRejection` by fixing the cause, not silencing it.

## React
- Hooks: complete dependency arrays, no hooks in conditions or loops. Keys are stable ids, never array indexes for reorderable lists.
- Derive values during render instead of copying props into state. Memoize only after measuring. Effects are for syncing with external systems, not for computing state.
- Fetch data through a caching data layer, not ad hoc effects. Clean up effects.

## Security
- Never `eval`, `new Function`, or set `innerHTML` with unescaped input; use `textContent` or a sanitizer (DOMPurify) when HTML is required. React's `dangerouslySetInnerHTML` is the same risk.
- `child_process.execFile` / `spawn` with an argument array, never `exec` with a built string. Validate untrusted JSON with a schema (zod, valibot, ajv) before use.
- Guard against prototype pollution when merging untrusted objects (reject `__proto__`, `constructor`, `prototype` keys; use `Object.create(null)` or `Map`).
- Servers: `helmet` or equivalent headers, rate limiting, CORS allowlist (never `*` with credentials), cookies `httpOnly`, `secure`, `sameSite`. No secrets in client bundles: anything shipped to the browser is public.

## Testing
- Test behavior through the public interface. Fake timers and network. For UI, query by role and label (Testing Library), not by implementation details.
