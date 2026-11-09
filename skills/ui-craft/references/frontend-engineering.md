---
name: frontend-engineering
description: Frontend engineering: component architecture, state, rendering and memory, forms, routing, bundle and asset performance, caching, optimistic updates. Use when building or changing UI code in React, Vue, Svelte, Angular or plain JS.
---

# frontend-engineering

Follow the project's framework and conventions. These rules apply on top.

## Components
- Organize as small components with one clear responsibility. Split a component that does data loading, state and a long render together; a component past a few hundred lines or with many unrelated props is too big.
- Build shared elements once: buttons, inputs, form fields, dialogs, tables, toasts live in a shared UI folder and are reused, not copy-pasted. Feature code composes them.
- Props in, events out. Keep presentational components free of data fetching; put fetching and side effects in hooks, containers or loaders.
- Use semantic HTML and accessible patterns inside components (labels, roles only where needed, focus management in dialogs and menus, keyboard support). See the adjacent `web-frontend.md` reference and the `language-standards` skill.
- Keep one design system: shared tokens and components. No one-off colors, spacing or font sizes; if a value is missing from the system, add it to the system.

## State
- Keep state as local as possible. Lift it only as far as needed. Use context or a store for truly cross-cutting state. Do not add a state library for what props and local state handle.
- Separate server state (cached remote data: use a data-fetching layer with caching, deduplication, retries and invalidation) from UI state (open panels, inputs, selected tab).
- Derive values during render instead of storing duplicates; one source of truth per fact. Keep UI state in sync with the server after mutations: invalidate or update the cache, never leave stale data on screen.
- Optimistic updates: apply the change immediately, keep the previous value, roll back and show an error if the request fails, and reconcile with the server response.

## States and interaction
- Every data view has loading, empty, error and success states; every control has default, hover, focus, active and disabled; every async action shows progress and failure. Errors tell the user what happened and what to do, without technical internals.
- Form validation gives clear inline messages, validates on the client for usability and always again on the server. Preserve user input on failure. Disable double submits.
- Interactions are predictable: the same control behaves the same way everywhere; destructive actions are confirmed or undoable.
- Routing: URLs reflect state worth sharing or bookmarking; back and forward work; unknown routes show a real 404; redirects after login restore where the user was; route guards are a convenience, never the security boundary.

## Rendering and memory
- Avoid unnecessary re-renders: stable props, keys that are ids, state close to where it is used, memoization only after measuring. Virtualize long lists. Debounce or throttle high-frequency handlers (scroll, resize, input).
- Clean up what you start: event listeners, timers, subscriptions, observers, WebSockets, in-flight requests (abort on unmount). Effects list complete dependencies.
- Minimize DOM work: batch reads and writes, avoid layout thrash, animate `transform` and `opacity`.

## Loading performance
- Fast first render: send less. Code-split by route and heavy component; lazy-load below-the-fold and non-critical code; defer third-party scripts.
- Optimize assets: responsive images with `srcset` and modern formats, width and height set, font subsets with `font-display: swap`, SVG for icons. Keep bundles small: analyze the bundle, remove unused dependencies, prefer small libraries, import only what you use (named imports, no whole-library imports).
- Cache deliberately: long-lived immutable caching for hashed static assets, short or validated caching for HTML and data, service workers only with a clear update strategy.
- Network efficiency: no redundant requests (deduplicate, cache, share in-flight requests), batch calls, request only needed fields, paginate or stream large data, cancel stale requests.
- Measure real performance: Lighthouse and the browser performance panel in development, field data (Core Web Vitals: LCP, INP, CLS) in production. Report numbers before and after a performance change.

## Compatibility
- Support the browsers the project targets (check `browserslist` or the stated support). Use feature detection and fallbacks, not user-agent checks. Test at mobile, tablet and desktop widths and with keyboard only.
