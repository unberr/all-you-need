---
name: ui-craft
description: Single entry for building, redesigning or reviewing any UI: web pages, dashboards, components, mobile screens. One decision path and precedence order for the design engines. Use for UI work.
paths:
  - "**/*.html"
  - "**/*.css"
  - "**/*.scss"
  - "**/*.vue"
  - "**/*.svelte"
  - "**/*.jsx"
  - "**/*.tsx"
---

# UI craft

One path for UI work. This skill decides which part of the visual and engineering guidance to use, so the rules stay consistent.

The component engineering and visual design guides are preserved as `references/frontend-engineering.md` and `references/web-frontend.md`. Read only the reference that applies to the current UI change; this skill already carries their shared accessibility and interaction floor.

## Precedence (higher wins)

1. The user's brief: pinned fonts, palettes, eras, references. Never redirect a clear brief toward house taste.
2. The project: `PRODUCT.md`, `DESIGN.md`, `design-system/<slug>/MASTER.md` (page file overrides master), existing tokens and components.
3. Art direction chosen by `design-taste-frontend` for new surfaces.
4. The rules below.

Refinement keeps the incumbent identity, copy and behavior outside scope. Redesign replaces the look but keeps content, function and native affordances. Never split the difference.

## 0. Plan, then check it against the defaults (from frontend-design)

Ground the design in the subject: its industry, materials and vernacular. If the brief names no subject, propose one (subject, audience, primary job) and confirm.

Before code, write a compact plan: 4 to 6 named hex colors, typefaces and their roles, a layout concept (one sentence plus an ASCII wireframe, with alignment), and the principles that make this page unique. Then review the plan: any part you would produce for any similar brief gets revised, and say what changed.

Unless the brief asks for them, these are defaults, not choices:
- cream background (near #F4F1EA) with serif display and terracotta accent (near #D97757);
- near-black with one acid-green or vermilion accent;
- broadsheet layout with hairline rules, zero radius, dense columns;
- the SaaS card kit: identical rounded cards, one radius everywhere, the same rgba(0,0,0,.1) shadow, gradient washes;
- template chrome: ALL-CAPS eyebrow over every heading, 'A · B · C' meta strings, 'WORD — fragment' labels, #0B0B0B or #111 instead of black, mono for small labels, '→' on every link;
- one accented word in a headline, numbered markers (01 / 02) on content that is not a sequence, fade-and-slide-up on every section, hover motion on every card, a big-number-plus-gradient hero.

Spend boldness in one place and keep the rest quiet; before shipping, remove one accessory. Watch CSS specificity between section and element selectors (padding and margin collisions).

## 1. Classify the surface (from impeccable)

Pick the mode from the surface, not the product:

- **Persuade**: landing, marketing, pricing. Go to section 2, then 4.
- **Operate**: app UI, dashboards, settings, admin. Scanability and convention beat expression. Go to 3 and 4.
- **Read**: docs, articles, changelogs. Structure for comprehension first.
- **Experience**: portfolio, gallery. The artifact leads; chrome recedes. Section 5 applies.

Mobile or native target: also apply section 3's mobile rules.

## 2. Persuade surfaces (from landing-page-design, Part A)

One offer, one audience, one primary action.

- **Intake**, asked in one batch, only what is missing: the one action, the offer, the ICP, top three objections, traffic source, proof assets, guarantees. If unanswered, state the assumption in one line and continue.
- **Above the fold**: outcome headline with audience, a subhead that says how, one CTA (verb plus what they get; never "Learn more" or "Submit"), one proof signal, a real product visual.
- **Argument**: problem to solution, 3 to 5 outcome benefits, how it works in 3 steps, proof placed beside the claim it supports.
- **Close**: FAQ (6 to 12), risk reversal (trial, cancel anytime, guarantee), final CTA identical to the top.
- **Copy**: specific numbers over "streamline" or "optimize". Benefit first, feature second. Mirror the ad headline when traffic is paid.
- **Build order**: hero, benefits, how it works, proof, FAQ, final CTA. Section by section; never regenerate the whole page per iteration.
- **SEO**: `noindex` ad-only or time-bound pages. Evergreen pages get title, meta description, internal links and FAQ in plain Q and A (FAQ schema when it fits).

## 3. Operate and mobile surfaces (from mobile-app-ui-design and ui-ux-pro-max)

- Primary actions in the thumb zone (bottom third). Touch targets at least 44x44 px with 8 px between.
- Bottom nav: 5 items max. Back behavior predictable; every view deep-linkable.
- Empty states carry guidance and a CTA. Every async action shows loading feedback.
- Type: one family (two max), at most 4 sizes and 2 weights per screen, tabular or mono figures for prices and metrics, body at least 16 px, text containers under 600 px wide.
- Color: 60 percent neutral, 30 percent secondary, 10 percent accent. Hierarchy through opacity of the text color (100, 80, 60 to 70). Strong colors only for meaningful states. Semantic tokens, never raw hex in components.
- Spacing on a 4/8 grid. Related items closer than unrelated ones; next group gap about 2x the inner gap.
- Shadows soft and tinted to the background, never pure black on color.
- Forms: visible labels (placeholder is not a label), error next to the field, helper text, progressive disclosure.
- Charts: legend and tooltips; never color alone to carry meaning.
- Design the peak moment and the end moment of a flow deliberately (confirmation, completion).

## 4. Floor for every surface (merged from all five; non-negotiable)

- Accessibility: contrast 4.5:1 text, 3:1 large text and UI; visible focus rings; keyboard reachable in logical order; labels on icon-only buttons; alt text; no information by color alone; zoom never disabled.
- Motion: animate only `transform` and `opacity`. Wrap continuous or large motion in `@media (prefers-reduced-motion: no-preference)`. Exit faster than enter; no single duration for everything. Set `will-change` only during the animation.
- Pointer effects (custom cursors, magnetic buttons, heavy hover) only inside `@media (hover: hover) and (pointer: fine)`.
- Layout: mobile first, no horizontal scroll, reserve space for media (CLS under 0.1), `100dvh` not `100vh` for full-height heroes.
- Assets: AVIF or WebP, lazy below the fold, SVG icons (no emoji as icons).
- UI copy: name things by what users understand ("notifications", not "webhook config"). Buttons say what happens ("Save changes", not "Submit"), and one action keeps its name through the flow ("Publish" leads to "Published"). Errors say what happened and how to fix it, without apology. Sentence case.
- Verify by looking: render at the shipped sizes (playwright-cli screenshots), batch fixes per look, then look again.

## 5. Ambitious visuals (from premium-frontend-ui)

Only for Persuade or Experience surfaces, or when the brief asks for it. Commit to one identity (editorial brutalism, organic fluid, technical, cinematic), never a mix.

- Fluid display type with `clamp()`; split headlines into words or chars (SplitType or GSAP SplitText) for staggered entrances, keeping the original text accessible.
- Scroll narrative with GSAP ScrollTrigger (pinned sections, horizontal galleries, restrained parallax). Use the installed `gsap-*` skills for API detail. Smooth scroll (Lenis) only when the brief wants it; it must not break anchor links or keyboard scrolling.
- Texture: noise overlay at 0.02 to 0.05 opacity; glass via `backdrop-filter` with a thin translucent border, and a solid fallback.
- No preloader unless real assets need it; a preloader must never delay content the user could already read.

## Engines (use the tool, not a copy of its rules)

| Job | Engine |
|---|---|
| Art direction for a new surface | Read `~/.claude/skills/design-taste-frontend/SKILL.md` and follow it |
| Palettes, font pairings, product-type patterns, stack guidelines, GSAP presets | `python3 ~/.claude/skills/ui-ux-pro-max/scripts/search.py "<2-5 terms>" --design-system` or `--domain <d>` or `--stack <s>`. One intent per query, retry once narrower, never present a 0-result search as data |
| Full UX rule text or app pre-delivery checklist | `~/.claude/skills/ui-ux-pro-max/references/quick-reference.md`, `pro-rules.md` |
| Named passes: critique, audit, polish, harden, distill, bolder, quieter, typeset, layout, colorize, animate, clarify, adapt, onboard, optimize | Read `~/.claude/skills/impeccable/reference/<command>.md` (native variants `*.native.md`); read `craft-floor.md` before any UI edit made through impeccable |
| Project context load (PRODUCT.md, DESIGN.md) | `~/.claude/skills/impeccable/scripts/impeccable context` once per session, from the project root |
| Industry conventions for an app category | `~/.claude/skills/mobile-app-ui-design/references/industry-conventions.md` |
| React or Next.js performance | `vercel-react-best-practices` |
| Final guideline check | `web-design-guidelines` |

Do not run an engine's persistence flags (`--persist --force`, impeccable `doctor`) unless the user asks.
