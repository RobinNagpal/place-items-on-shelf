# Design System — Marketing Flyer

The visual rules for the four-page flyer. Lifted from the existing
KoalaGains "GenAI Simulations For Every Business School" flyer so the
new pages look like part of the same family.

## Page format

| Property | Value |
|----------|-------|
| Size | US Letter portrait, **8.5 × 11 in** (816 × 1056 px at 96 dpi) |
| Orientation | Portrait, on every page |
| Margins | **0.5 in / 12 mm** on all four sides |
| Grid | Single column. No multi-column layouts. |

Pick US Letter or A4 once and use the same size on all four pages.

## Colors

Hex values, taken from the KoalaGains reference flyer. The
background is the dominant dark navy; everything else sits on top.

| Role | Hex | Notes |
|------|-----|-------|
| Background | `#1A2747` | Deep navy, fills the whole page. |
| Heading text | `#FFFFFF` | Pure white. |
| Body text | `#D6DDE8` | Soft off-white — easier on the eye than pure white at 11 pt. |
| Accent bar | `#5F86FF` | 4 px wide vertical bar to the left of every section heading. |
| Bullet marker | `#9B73FF` | Small filled circle (8 px) in front of every bullet. |
| Card border | `#2E406B` | 1 px line around each bullet card (optional). |
| Footer text | `#7A8AAA` | Muted blue-grey, smaller than body. |

If a page uses card-style bullets (boxed text), fill the card with
`#22305A` and keep the same 1 px `#2E406B` border. Plain bullets
without a card work too — pick one style per page and stick to it.

## Type

A clean grotesque sans-serif. Inter is the default; DM Sans, Manrope,
or Work Sans are acceptable substitutes.

| Block | Size | Weight |
|-------|------|--------|
| Page title (e.g. "Simulation Setup") | 36 pt | Bold |
| Section heading (e.g. "What We Build") | 22 pt | Bold |
| Bullet heading | 14 pt | Semibold |
| Body text | 11 pt | Regular |
| Footer | 9 pt | Regular |

Line height is **1.4 ×** the font size for all body text.

## Layout pattern

Every page uses the same skeleton:

```
+-----------------------------------------+
|                              [DoDAO ▢] |  logo top-right
|                                         |
|  ▎Page Title                            |  accent bar + 36 pt title
|                                         |
|  One-sentence intro under the title.    |  11 pt body
|                                         |
|  ▎Section Heading                       |  accent bar + 22 pt heading
|                                         |
|  • Bullet Heading                       |  14 pt semibold
|    1–2 sentence body.                   |  11 pt body
|                                         |
|  • Bullet Heading                       |
|    1–2 sentence body.                   |
|                                         |
|  ▎Section Heading                       |
|  ...                                    |
|                                         |
|  For more information, visit            |  footer, 9 pt
|  https://dodao.io        Page N of 4    |
+-----------------------------------------+
```

Rules:

- The DoDAO logo sits in the **top-right** corner on every page.
- Every section heading has a **4 px vertical accent bar** in
  `#5F86FF` immediately to its left, with a 12 px gap between bar
  and text.
- Every bullet has a **small filled circle** (`#9B73FF`, 8 px) as its
  marker, vertically centered with the first line of the bullet heading.
- The footer repeats verbatim on every page: URL on the left,
  "Page N of 4" on the right. Both in `#7A8AAA`.
- Vertical spacing between blocks: 24 px after a section heading,
  16 px between bullets, 32 px before the next section heading.

## What not to do

- No drop shadows, gradients, or glass effects.
- No stock photos of robots or factories. The pages are typographic.
- No emojis or decorative icons in the body.
- No reverse-video text (white text on a colored highlight strip).
- No two different fonts on the same page.
- No "Lorem ipsum"-style filler bullets — every bullet says something
  concrete or it gets cut.
- No screenshots or charts on these four pages. If we add them later,
  they get their own page and their own design pass.

## Asset checklist before exporting

- [ ] DoDAO logo PNG at 2× resolution, transparent background.
- [ ] Final URL for the footer (`dodao.io` or specific landing page).
- [ ] Real email address on Page 4 (placeholder `contact@dodao.io`
      replaced with the address that actually receives mail).
- [ ] Calendly / booking link confirmed.
- [ ] Page numbers updated to "Page 1 of 4" through "Page 4 of 4"
      (not "Page X of 5" — that was the KoalaGains reference).
