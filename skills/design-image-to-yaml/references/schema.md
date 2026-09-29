# Design spec YAML schema

Every spec has five top-level keys, in this order. Keeping the order fixed means a
developer who has read one spec can skim the next one.

```yaml
meta:        # what was analyzed, how confident the extraction is, open questions
tokens:      # colors, fonts, spacing, radii, shadows — defined once, referenced by name
layout:      # page-level grid / breakpoints / max-width
structure:   # the HTML tree — the main deliverable
copy:        # every string of visible text, keyed by id, referenced from structure
```

Optional trailing sections: `components` (repeated patterns extracted once),
`interactions` (hover/focus/state guesses), `assets` (images/icons to source),
`accessibility` (landmark roles, contrast results, missing alt text).

---

## `meta`

```yaml
meta:
  source: hero-mockup.png            # filename or description of the image
  image_size: 1440x900               # px, from the palette script
  viewport_guess: desktop            # desktop | tablet | mobile | unknown
  target: html-css                   # html-css | tailwind | react-css-modules | ... (what the dev asked for)
  confidence:
    layout: high                     # high | medium | low
    colors: high                     # high when measured with the script, medium/low when estimated
    fonts: medium                    # fonts are almost never "high" from a raster image
    copy: high                       # low if text is tiny, blurred, or partially cropped
  open_questions:                    # things the image cannot answer — ask the designer
    - "Is the nav sticky on scroll?"
    - "Mobile layout not shown — assume single column?"
```

## `tokens`

Colors carry a `value` and a `usage` so a dev knows *why* the color exists, not just that
it does. Name tokens by role (`brand-primary`, `surface`, `text-muted`), never by hue
(`blue-1`), because roles survive a rebrand and hues do not.

```yaml
tokens:
  colors:
    brand-primary:   { value: "#2563EB", usage: "primary buttons, links" }
    brand-primary-hover: { value: "#1D4ED8", usage: "estimated hover state, ~10% darker", estimated: true }
    surface:         { value: "#FFFFFF", usage: "page background" }
    surface-alt:     { value: "#F8FAFC", usage: "card and section backgrounds" }
    text:            { value: "#0F172A", usage: "headings, body" }
    text-muted:      { value: "#64748B", usage: "captions, helper text" }
    border:          { value: "#E2E8F0", usage: "card outlines, dividers" }
  fonts:
    heading:
      family: "Inter"                 # best guess
      fallback: "ui-sans-serif, system-ui, sans-serif"
      evidence: "geometric sans, single-story a, wide apertures — could also be SF Pro or Manrope"
      weights: [600, 700]
    body:
      family: "Inter"
      fallback: "system-ui, sans-serif"
      weights: [400, 500]
  type_scale:                        # px measured or estimated from the image
    display: { size: 56, line_height: 1.1, weight: 700, letter_spacing: "-0.02em" }
    h2:      { size: 36, line_height: 1.2, weight: 700 }
    body:    { size: 16, line_height: 1.6, weight: 400 }
    small:   { size: 14, line_height: 1.5, weight: 400 }
  spacing:                           # base unit + the values actually observed
    base: 4
    observed: [8, 12, 16, 24, 32, 48, 96]
  radii:
    sm: 6
    md: 12
    pill: 9999
  shadows:
    card: "0 1px 3px rgba(15, 23, 42, 0.08)"
```

## `layout`

```yaml
layout:
  max_width: 1200                    # content container in px
  gutter: 24
  grid: { columns: 12, gap: 24 }
  breakpoints_suggested:             # image shows one viewport; suggest where to break
    md: 768
    lg: 1024
  sections_in_order: [header, hero, features, testimonial, footer]
```

## `structure`

A tree of nodes. Each node maps to one element. Keep it semantic: the point of this
file is to hand the developer *decisions* (this is a `<nav>`, this is an `<h1>`, these
cards are an `<ul>`), so avoid `div` unless nothing better fits — and when you must use
`div`, say why in `note`.

```yaml
structure:
  - tag: header
    role: banner
    classes: [site-header]            # suggested class names (BEM-ish, kebab-case) — or Tailwind utilities if target is tailwind
    style:                            # only the properties needed to reproduce the look; reference tokens by name
      background: surface
      border_bottom: "1px solid border"
      padding: "16px 24px"
    layout: { display: flex, justify: space-between, align: center }
    children:
      - tag: a
        href: "/"
        aria_label: "Acme home"
        children:
          - tag: img
            src: "assets/logo.svg"      # what to source, not a real path
            alt: "Acme"
            size: { width: 120, height: 32 }
      - tag: nav
        aria_label: "Primary"
        children:
          - tag: ul
            classes: [nav-list]
            layout: { display: flex, gap: 32 }
            children:
              - tag: li
                children:
                  - { tag: a, href: "#", copy: nav.features, style: { color: text, font: body } }
      - tag: a
        classes: [btn, btn-primary]
        href: "#"
        copy: nav.cta
        style: { background: brand-primary, color: surface, radius: md, padding: "10px 20px", font: body, weight: 600 }
        note: "Rendered as <a> because it navigates; use <button> if it opens a modal."
  - tag: main
    children:
      - tag: section
        classes: [hero]
        aria_labelledby: hero-title
        children:
          - { tag: h1, id: hero-title, copy: hero.title, style: { font: heading, size: display, color: text } }
```

Node fields (all optional except `tag`):

| field | meaning |
|---|---|
| `tag` | the HTML element |
| `role`, `aria_label`, `aria_labelledby`, `id`, `href`, `src`, `alt`, `type` | attributes, written as-is |
| `classes` | suggested class names (or Tailwind utilities when `meta.target: tailwind`) |
| `style` | visual properties; color/font values reference `tokens` by name, sizes reference `type_scale` |
| `layout` | box behaviour: `display`, `direction`, `justify`, `align`, `gap`, `columns`, `wrap` |
| `size` | measured `{ width, height }` in px when it matters (logos, images, fixed cards) |
| `copy` | id into the top-level `copy` map — never inline the text here |
| `component` | name of an entry in `components` when this node is an instance of a repeated pattern |
| `repeat` | for lists: how many instances the image shows, e.g. `repeat: 3` |
| `note` | any judgement call the dev should know about |
| `children` | nested nodes |

## `copy`

Every visible string, verbatim, keyed by a dotted id that mirrors the structure. Verbatim
means keep the designer's capitalization, punctuation, and line breaks (`|` block scalar
for multi-line). If a word is unreadable, write `[illegible]` rather than guessing —
a dev can ask; a wrong word silently ships.

```yaml
copy:
  nav.features:   { text: "Features" }
  nav.cta:        { text: "Get started" }
  hero.title:
    text: |
      Ship your ideas
      faster than ever
    note: "Two lines in the design; line break is intentional"
  hero.subtitle:  { text: "The toolkit modern teams use to build, test and launch." }
  hero.cta_primary:   { text: "Start free trial" }
  hero.cta_secondary: { text: "Watch demo →", note: "Arrow is a glyph in the text, not an icon" }
  features.card_1.title: { text: "Instant deploys" }
  features.card_1.body:  { text: "Push to main and your changes are live in seconds." }
  footer.legal:   { text: "© 2026 Acme, Inc. All rights reserved." }
```

## `components` (optional)

When the same visual pattern appears more than once (cards, list rows, pricing tiers),
define it once here and reference it from `structure` with `component:` so the developer
knows it should be one React component / one partial, not three copies.

```yaml
components:
  feature-card:
    tag: article
    classes: [feature-card]
    style: { background: surface-alt, radius: md, padding: 24, border: "1px solid border" }
    slots: [icon, title, body]
    instances: 3
```

## `accessibility` (optional but encouraged)

```yaml
accessibility:
  landmarks: [header/banner, nav, main, footer/contentinfo]
  heading_order: [h1, h2, h2, h2, h3, h3, h3]
  contrast_checks:                   # from extract_palette.py --contrast
    - { fg: text-muted, bg: surface, ratio: 4.6, passes: AA }
    - { fg: surface, bg: brand-primary, ratio: 5.2, passes: AA }
  concerns:
    - "Placeholder text in search input is #A0AEC0 on white — 2.5:1, fails AA"
```
