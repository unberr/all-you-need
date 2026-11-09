# TypeScript (read javascript.md as well)

## Toolchain
- Type check: `tsc --noEmit` (or the project's `typecheck` script). Lint with `typescript-eslint`. Config in `tsconfig.json`.
- Compiler options to expect and keep: `"strict": true`, and ideally `noUncheckedIndexedAccess`, `noImplicitOverride`, `noFallthroughCasesInSwitch`. Never loosen `strict` to make an error go away.

## Idioms that prevent defects
- No `any`. Use `unknown` for untrusted values and narrow it. `as` casts and non-null `!` assertions are claims the compiler cannot check: prefer type guards, `satisfies`, or fixing the type.
- Types vanish at runtime. Validate data entering the system (HTTP bodies, JSON files, environment, `localStorage`) with a runtime schema (zod, valibot) and infer the type from the schema, so type and check cannot drift.
- Model states as discriminated unions with a literal `kind`/`type` tag, and make `switch` exhaustive with a `never` check, so adding a variant breaks the build where it must.
- Prefer unions of string literals or `as const` objects over `enum`. Use `readonly` and `Readonly<T>` for data that must not change.
- Use `interface` for object shapes that may be extended, `type` for unions, intersections and mapped types; be consistent with the project.
- Keep generics constrained (`T extends ...`) and name them by role when there are several. Do not use generics where a concrete type works.
- `import type` for type-only imports. Avoid barrel files that create cycles or defeat tree shaking.
- Return types explicit on exported functions so API changes are deliberate. Let the compiler infer locals.
- Handle `null` and `undefined` explicitly. Optional properties and `T | undefined` are different: pick one meaning.

## Lint rules worth keeping on
`no-floating-promises`, `no-misused-promises`, `no-explicit-any`, `no-unsafe-*` family, `consistent-type-imports`, `switch-exhaustiveness-check`.

## Testing
- Type tests for public generic APIs (`expectTypeOf` in vitest, or `tsd`). Test runtime validation with bad input, not only good input.
