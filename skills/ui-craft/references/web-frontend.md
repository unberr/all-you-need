---
name: web-frontend
description: Visual design and frontend quality: hierarchy, type and spacing scales, color and contrast, responsive layout, states, motion, accessibility, performance targets, anti-slop checks. Use when designing or building any UI.
---

# web-frontend

Design is decisions made once and applied everywhere. Make the decisions first, as tokens, then build.

## 1. Before pixels
- Who uses this and what is the one job of the page or screen? The primary action gets the most visual weight; everything else is quieter.
- Real content first. Design with real headings, real lengths and real data (including empty, long and error cases). No lorem ipsum.

## 2. Tokens (CSS custom properties; reuse, never hardcode)
- **Spacing:** one scale on a 4 or 8 px base (4, 8, 12, 16, 24, 32, 48, 64). Related things closer, unrelated things further.
- **Type:** 1 or 2 families. A modular scale (ratio 1.2 to 1.25). Body 16 px or larger, line-height 1.4 to 1.6, line length 45 to 75 characters. A clear weight hierarchy; avoid more than 3 sizes per screen section.
- **Color:** a neutral ramp plus one accent. Semantic colors for success, warning, error, info. Define light and dark themes through variables, not duplicated rules.
- **Shape and depth:** one radius scale, one shadow scale, one border treatment. Consistency reads as quality.
- **Layers:** a named z-index scale. No arbitrary `z-index: 9999`.

## 3. Layout and responsiveness
- Mobile first. Add breakpoints where the content breaks, not at device names. Use grid for two-dimensional layout, flex for one-dimensional, `gap` for spacing.
- Fluid sizes with `clamp()`, `min()` and `max()`. Container queries for components that live in different widths.
- Nothing scrolls horizontally at 320 px width. Text can be zoomed to 200% without loss. Respect safe areas on mobile.
- Align to a grid and a shared left edge. Group with space before reaching for borders and boxes.

## 4. Every interactive element has every state
Default, hover, focus-visible, active, disabled, loading, and where data is involved: empty, error, success. A page without these states is unfinished.
- Focus is always visible, with a style at least as clear as the default browser ring.
- Touch targets at least 24 by 24 CSS px (WCAG 2.2 minimum), 44 by 44 preferred.
- Buttons do actions, links navigate. Destructive actions are confirmed or undoable.
- Forms: visible labels, inline errors tied to the field and announced, helpful validation messages, correct `type` and `autocomplete`.

## 5. Accessibility (aim for WCAG 2.2 AA)
- Contrast: 4.5:1 for normal text, 3:1 for large text and UI components. Never rely on color alone to carry meaning.
- Semantic HTML before ARIA. Landmarks, one `h1`, headings in order. ARIA only to fill a real gap, and keep its state in sync.
- Everything works by keyboard in a logical order, with no traps. Modals trap focus and restore it on close.
- Respect `prefers-reduced-motion`, `prefers-color-scheme` and user font-size settings.
- Images have meaningful `alt` (empty `alt=""` when decorative). Media has captions or transcripts.

## 6. Motion
- Motion explains change (where something came from, what changed); it is not decoration. 150 to 300 ms for UI feedback, easing out for entering, easing in for leaving.
- Animate `transform` and `opacity`. Avoid animating layout properties. Provide a reduced-motion alternative.

## 7. Performance targets (Core Web Vitals, good thresholds)
- Largest Contentful Paint under 2.5 s, Interaction to Next Paint under 200 ms, Cumulative Layout Shift under 0.1.
- Set `width` and `height` (or `aspect-ratio`) on images and embeds. Lazy-load below the fold. Responsive images with `srcset`. Preload only the critical font and hero image.
- Ship less JavaScript: split by route, defer non-critical scripts, remove unused dependencies, avoid layout thrashing in handlers.
- Measure with Lighthouse or the browser performance panel before and after; do not guess.

## 7b. Anti-slop checklist (reject any that apply)
Generic purple-to-blue gradient hero with a floating card; mixed random font stacks; emoji used as icons; every section centered with identical card grids; inconsistent radii and shadows; low-contrast gray-on-gray text; placeholder copy; stock illustration with no relation to the product; animations on everything; layout that falls apart at 320 px or 1920 px wide.

## 8. Verify
Open the page at 320, 768 and 1280 px wide. Tab through it. Run an accessibility check (axe or Lighthouse) and read the real result. Check it in dark mode and with reduced motion on. Say which of these you did not do.

If art-direction skills are installed (`ui-craft`, `design-taste-frontend`), use them to choose the visual direction, and keep this skill's rules as the quality floor.
