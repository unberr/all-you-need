# HTML and CSS (visual design rules: skill `references/web-frontend.md`)

## Checks
- Validate HTML (the W3C validator or `html-validate`), lint CSS with `stylelint` when configured, and run an accessibility check (axe or Lighthouse). Read the real output.

## HTML
- Start with `<!doctype html>`, `<html lang="...">`, `<meta charset="utf-8">` and `<meta name="viewport" content="width=device-width, initial-scale=1">`. Never block zoom (`user-scalable=no`, `maximum-scale=1`).
- Semantic structure: `header`, `nav`, `main` (one), `section` with a heading, `article`, `aside`, `footer`. One `h1`; headings descend in order without skipping levels. Lists for lists, `table` for tabular data only.
- Interactive controls: `<button type="button">` for actions, `<a href>` for navigation. Never `div` or `span` with `onclick`; never `href="#"` as a button. Every control reachable and operable by keyboard.
- Forms: every input has a `<label for>` (or wraps it), the right `type`, `name`, `autocomplete`, `required` and validation attributes. Group related inputs with `fieldset` and `legend`. Tie error text to the field with `aria-describedby`.
- Images: meaningful `alt` text, or `alt=""` when decorative; `width` and `height` set; `loading="lazy"` below the fold; `srcset` and `sizes` for responsive images; `<picture>` for format or art direction.
- Scripts: `defer` (or `type="module"`) by default; no inline event handlers or inline scripts, so a strict Content Security Policy works. Third-party scripts and styles from a CDN carry `integrity` and `crossorigin`. Links with `target="_blank"` carry `rel="noopener"`.
- Metadata that matters: a unique `<title>`, `meta name="description"`, canonical link, Open Graph tags for shared pages.
- Never put untrusted input into HTML without encoding it for its context (text, attribute, URL, script).

## CSS
- Tokens as custom properties on `:root` (colors, spacing, type, radius, shadow). Components use tokens, never raw values.
- `box-sizing: border-box` globally. Relative units: `rem` for type and spacing, `%`/`fr`/`ch` for layout, `px` for borders and hairlines. Fluid sizing with `clamp()`. `dvh` instead of `vh` for full-height mobile layouts.
- Layout with grid and flexbox and `gap`; do not use floats or `position: absolute` for layout. Logical properties (`margin-inline`, `padding-block`) so right-to-left works.
- Mobile first: base styles for small screens, `@media (min-width: ...)` to add. Container queries (`@container`) for components.
- Keep specificity low and flat: class selectors, no IDs for styling, no deep descendant chains, no `!important` except to override third-party code or utilities. Use `@layer` to control order, `:where()` to zero specificity.
- Never remove focus outlines without a replacement: style `:focus-visible` clearly. Do not hide content with `display: none` that screen readers should read; use a visually-hidden utility.
- Respect user preferences: `@media (prefers-reduced-motion: reduce)` turns off non-essential motion, `prefers-color-scheme` for dark mode, `color-scheme` property for native controls.
- Animate `transform` and `opacity`. Set `aspect-ratio` for media. `font-display: swap` with a metric-compatible fallback font. Define a z-index scale.
- Contrast: 4.5:1 for normal text, 3:1 for large text and UI parts, checked on every state and theme.
- Remove dead CSS; do not leave commented-out blocks. Prefer native features (nesting, `:has()`, `color-mix()`, container queries) when the project's browser support allows.
