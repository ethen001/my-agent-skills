---
name: design-image-to-yaml
description: Convert a screenshot, mockup, wireframe, Figma export, or any UI/design image into a developer-ready YAML spec — recommended semantic HTML structure, CSS classes/styles or Tailwind utilities, exact measured colors, best-guess fonts and type scale, and every string of visible copy extracted verbatim. Use this whenever someone shares a design image and wants to build it, "translate it to code", get a handoff spec, "extract the text/colors/fonts", or asks what HTML/CSS a design should be — even if they don't say "YAML". Also use it when a dev wants a readable, reviewable intermediate file before implementing a design in React, Vue, plain HTML, or a micro frontend.
---

# Design image → YAML spec

Turn a picture of a UI into a file a developer can read in two minutes and implement
without re-deriving every decision. The YAML is the deliverable; the developer never
has to look at the image again unless the spec says "check the image".

The spec has five fixed sections — `meta`, `tokens`, `layout`, `structure`, `copy` —
plus optional `components`, `interactions`, `assets`, `accessibility`. Full field
reference with examples: `references/schema.md`. A complete worked example — input
image plus the finished spec — is in `references/example-input.png` and
`references/example-spec.yaml`; skim the example once so you know what "done" looks
like, then keep the schema open while writing.

## Why YAML and why this shape

Developers implementing from a mockup make dozens of small decisions: is that a
`<button>` or an `<a>`? Is this heading an `h2` or `h3`? Is the grey `#64748B` or
`#6B7280`? Are these three cards one component? Each decision is cheap but they add up,
and every dev makes them slightly differently. The spec makes those decisions once, in
writing, where a designer or lead can review them *before* anyone writes code. That is
why the file leans on judgement calls (`note:` fields, `open_questions`, confidence
levels) rather than pretending to be a pixel dump.

## Workflow

### 1. Look at the whole image first

Before measuring anything, describe to yourself what the page *is*: a marketing hero,
a settings form, a dashboard, a mobile onboarding screen. Identify the major regions
top-to-bottom (header, hero, feature grid, footer...) and how many distinct visual
"blocks" there are. This sets the `layout.sections_in_order` and keeps the `structure`
tree from becoming a flat list of rectangles.

Note the viewport: a 1440-wide image is a desktop design; 375–430 is mobile. Record
this in `meta.viewport_guess` — it changes which breakpoints you suggest.

### 2. Measure colors — don't estimate them

Vision estimates of hex values are reliably off by 5–15 per channel, which is the
difference between a brand blue and a slightly wrong blue that a designer will bounce.
Measure instead:

```bash
python scripts/extract_palette.py mockup.png --top 12          # overall palette + coverage %
python scripts/extract_palette.py mockup.png --region 0,0,1440,72   # e.g. just the navbar
python scripts/extract_palette.py mockup.png --point 812,388    # a single button pixel
python scripts/extract_palette.py mockup.png --contrast "#64748B" "#FFFFFF"   # WCAG ratio
```

Use `--region` on each major section and `--point` on small targets (buttons, links,
icons) whose color would be drowned out in a whole-image histogram. Coverage
percentages tell you which color is the page background versus an accent.

If the script isn't available, run this inline (Pillow is almost always present):

```python
from PIL import Image; from collections import Counter
im = Image.open("mockup.png").convert("RGB"); im.thumbnail((600, 600))
groups, exact = Counter(), {}
for p in im.getdata():                      # group on a coarse grid, report the exact mode
    k = tuple(c // 4 for c in p); groups[k] += 1; exact.setdefault(k, Counter())[p] += 1
for k, n in groups.most_common(12):
    print("#%02X%02X%02X" % exact[k].most_common(1)[0][0], round(100 * n / sum(groups.values()), 1), "%")
```

Report the exact pixel value, not a bucket average — a quantized `#FCFCFC` where the
design says `#FFFFFF` is the kind of drift this whole step exists to prevent.

Name every color by **role** (`brand-primary`, `surface`, `text-muted`), not by hue.
Add a `usage` string so a dev knows where it goes. If you invent a state color the image
doesn't show (hover, focus), include it but mark `estimated: true`.

### 3. Identify fonts honestly

A raster image cannot tell you the font with certainty, and a wrong confident guess
wastes a dev's afternoon hunting a license. Give a best guess with the *evidence*
(geometric vs humanist sans, single- vs double-story `a` and `g`, serif style, x-height,
distinctive glyphs like `R`, `Q`, `1`) and one or two alternates, plus a system fallback
stack. Set `meta.confidence.fonts` to `medium` at best unless the design shows a font
name or the user tells you. Do record what you *can* measure: weights in use, approximate
sizes (compare cap height against known element heights), line-height ratio, letter
spacing, and whether headings are tight-tracked.

### 4. Extract copy verbatim

Every visible string goes in `copy`, keyed by a dotted id that mirrors the structure
(`hero.title`, `features.card_2.body`, `footer.legal`). Preserve capitalization,
punctuation, glyphs (`→`, `•`), and intentional line breaks (use a `|` block scalar).
Placeholder text inside inputs is copy too. If a word is unreadable, write
`[illegible]` — never guess. A misread word ships silently; `[illegible]` gets asked
about. Nodes in `structure` reference copy by id and never inline the text, so a content
editor can review the copy section alone.

### 5. Build the structure tree

Walk the regions from step 1 and turn each into semantic elements. The valuable part is
the decision, so prefer the specific element and explain the borderline ones in `note:`.

- Landmarks first: `header`, `nav`, `main`, `section` (with `aria-labelledby`),
  `aside`, `footer`.
- One `h1`; heading levels follow visual hierarchy, not visual size (a big number in a
  stat tile is a `p`/`strong`, not an `h2`).
- Repeated visuals (cards, rows, tiers) → an `ul`/`li` or a `component` entry with
  `instances: N`, not N copies. This is what tells a React dev "make one component".
- `button` performs an action; `a` navigates. If the image can't tell you, pick `a`
  and say so in `note`.
- `img` needs `alt`; decorative images get `alt: ""` and a note.
- `div`/`span` only when nothing semantic fits, with a `note` saying why.

Attach `style` (referencing tokens by name) and `layout` (flex/grid intent, gaps,
alignment) to each node. Keep `style` to what's needed to reproduce the look; don't
list every CSS property. Measure `size` in px only where it matters — logos, hero
images, fixed-width cards, icon buttons.

### 6. Match the developer's target

Check what they're building with. If they mention Tailwind, put utilities in `classes`
(`[flex, items-center, gap-8, px-6]`) and still keep `tokens` so they can extend
their theme. If they mention CSS Modules, BEM, styled-components or a design system,
name classes to fit (`.hero__title`, `HeroTitle`, `Button variant="primary"`). Default
to kebab-case BEM-ish class names with plain CSS values. Record the choice in
`meta.target`.

For a micro-frontend or component-library context, the `components` section becomes the
most important part — group by what would become a separate component and name the
slots.

### 7. Record uncertainty and finish

Fill `meta.confidence` per area and `meta.open_questions` with everything the image
can't answer (sticky nav? hover states? mobile layout? what's behind the truncated
text?). Run the accessibility contrast checks on text/background pairs and list
failures under `accessibility.concerns` — catching a 2.5:1 placeholder before it ships
is exactly the kind of thing this spec is for.

Then validate:

```bash
python scripts/validate_spec.py spec.yaml
```

It catches unknown token references, missing copy ids, `div`s with no rationale, and
`img`s without alt. Fix errors; use warnings as prompts.

Save as `<name>-spec.yaml` next to the image and hand it over with a two-line summary:
what the page is, and the one or two open questions that most need a designer's answer.

## Output shape at a glance

```yaml
meta:      { source, image_size, viewport_guess, target, confidence: {layout, colors, fonts, copy}, open_questions: [] }
tokens:    { colors: {role: {value, usage}}, fonts: {heading, body}, type_scale, spacing, radii, shadows }
layout:    { max_width, gutter, grid, breakpoints_suggested, sections_in_order }
structure: [ { tag, role, classes, style, layout, copy, children: [...] } ]
copy:      { dotted.id: { text, note? } }
components:    { name: { tag, classes, style, slots, instances } }   # optional
accessibility: { landmarks, heading_order, contrast_checks, concerns } # optional
```

## Things that go wrong

- **Flat structure.** Forty sibling nodes under `body` means step 1 was skipped. Group
  into sections.
- **Inline copy.** Text inside `structure` nodes instead of `copy` ids — reviewers of
  copy have to read the whole tree.
- **Confident fonts.** "Font: Helvetica Neue" with no evidence. Give evidence and
  alternates.
- **Eyeballed hex.** Always measure; the script exists so this never has to be a guess.
- **Hue-named tokens.** `blue-500` tells a dev nothing about where it's used.
- **Pixel-perfect padding on everything.** Record the spacing *scale* (`4/8/16/24/32`)
  and use it; per-element px only where the design clearly breaks the scale.
- **Skipping states.** Inputs, buttons and links have hover/focus/disabled states the
  image can't show. Note the gap in `interactions` or `open_questions` rather than
  silently omitting it.

## Multiple images

Several screens of the same product: one spec per screen, but share `tokens` — extract
the palette from all images together (`--top 16` on each, then reconcile) so the design
tokens are consistent, and put shared components in the first spec's `components` with
a `shared_with:` list. A desktop and mobile view of the *same* page go in one spec with
`layout.responsive` describing what changes at each breakpoint.
