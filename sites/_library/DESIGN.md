---
name: SiteForge section library
description: Four style presets for Irish trades and local businesses, all driven by the business's own brand colour.
colors:
  accent: "var(--accent)"
  heritage-limestone: "#F2F0EB"
  heritage-ink: "#1C1E1B"
  heritage-muted: "#595C55"
  heritage-rule: "#D5D3CF"
  industrial-ground: "#101010"
  industrial-plate: "#1C1C1C"
  industrial-text: "#EDEDED"
  industrial-muted: "#A3A3A3"
  industrial-rule: "#333333"
  clean-white: "#FFFFFF"
  clean-mist: "#F4F4F4"
  clean-ink: "#15201C"
  clean-muted: "#52605A"
  clean-rule: "#DEDEDE"
  bold-paper: "#FFFFFF"
  bold-black: "#0B0B0B"
  bold-muted: "#454543"
typography:
  heritage-display:
    fontFamily: "Brygada 1918, Georgia, serif"
    fontWeight: 600
    lineHeight: 1.06
    letterSpacing: "-0.01em"
  heritage-body:
    fontFamily: "Libre Franklin, system-ui, sans-serif"
    fontSize: "1.0625rem"
    lineHeight: 1.65
  industrial-display:
    fontFamily: "Big Shoulders Display, Arial Narrow, sans-serif"
    fontWeight: 800
    lineHeight: 0.95
    letterSpacing: "0.005em"
  industrial-body:
    fontFamily: "Barlow, system-ui, sans-serif"
    fontSize: "1.0625rem"
    lineHeight: 1.6
  clean-display:
    fontFamily: "Bricolage Grotesque, system-ui, sans-serif"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "-0.03em"
  clean-body:
    fontFamily: "Figtree, system-ui, sans-serif"
    fontSize: "1.0625rem"
    lineHeight: 1.6
  bold-display:
    fontFamily: "Epilogue, system-ui, sans-serif"
    fontWeight: 800
    lineHeight: 0.94
    letterSpacing: "-0.04em"
  bold-body:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.0625rem"
    lineHeight: 1.55
rounded:
  heritage: "3px"
  industrial: "0px"
  clean-local: "14px"
  clean-local-button: "999px"
  bold: "0px"
spacing:
  gutter: "clamp(1rem, 4vw, 2.5rem)"
  heritage-section: "clamp(4.5rem, 9vw, 8rem)"
  industrial-section: "clamp(4rem, 8vw, 7rem)"
  clean-local-section: "clamp(3.5rem, 7vw, 6.5rem)"
  bold-section: "clamp(4.5rem, 10vw, 9rem)"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "var(--accent-fg)"
    padding: "0.95rem 1.5rem"
    height: "52px"
---

# Design System: SiteForge section library

## Overview

**Creative North Star: "The Van and the Map"**

A tradesperson's real brand lives on the side of their van: the name, the trade, a phone number big enough to read at a junction, and the towns they cover. It's plain, confident and local. The library takes that grammar and adds the other thing every local business is defined by: *where* it works. Town names are treated as content, not a footnote. The coverage line sits in the first screen of every hero, and the service-area section is a first-class part of the page.

The four presets are four rooms in the same house. They share one section grammar (the same slots, the same content keys, one sticky call bar), but each has its own type pairing, spacing rhythm, corner language and colour roles. The business's brand colour arrives at build time as `--accent` and is recomputed for contrast (`--accent-ink`, `--accent-fg`), so a pale yellow logo never produces unreadable text.

**Rejected:** Wix/FCR Media template looks, stock-photo collages, SaaS hero patterns (centred headline, gradient blob, logo cloud), purple gradients, fake urgency, eyebrow labels above headings, icon-tile card grids as page structure, and glassmorphism.

**Key Characteristics:**
- The phone number is typography, not a button label. It's set large wherever the layout gives it room.
- Towns are named in the first viewport.
- One accent, used with intent: buttons, the coverage pin, key rules and, in `bold` and `clean-local`, whole CTA fields.
- Every variant looks finished with no images.

## Colors

Each preset owns its neutrals. The accent is the only colour that comes from the business.

### Primary
- **Brand accent** (`--accent`, from the lead's brand colour): primary buttons, the location pin, active states, selection, focus rings, CTA fields in `clean-local` and `bold`.
- **Accent ink** (`--accent-ink`): the accent adjusted to at least 4.5:1 against the preset background. It's used when the accent sets text (links, the phone number, step numbers).
- **Accent foreground** (`--accent-fg`): black or white, whichever reads on the accent.

### Neutral (per preset)
- **heritage:** Limestone ground (#F2F0EB), white surfaces, Near-Black Ink (#1C1E1B), Moss Grey muted (#595C55), Stone rule (#D5D3CF). The "fascia" band is the accent sunk into near-black (`color-mix(in oklab, accent 26%, #121411)`), like a painted shopfront board.
- **industrial:** Charcoal ground (#101010), Plates (#1C1C1C, #262626), Chalk text (#EDEDED), Concrete muted (#A3A3A3), Seam lines (#333333), all true neutral (R=G=B). The band is near-black (#08090A).
- **clean-local:** White ground, Mist surfaces (#F4F4F4, #EAEAEA), Deep Green-Black ink (#15201C), Sage muted (#52605A), Soft rule (#DEDEDE). The band is the accent itself.
- **bold:** Paper white, Bone surface (#F0F0F0), True Black (#0B0B0B) for text, rules and band, Graphite muted (#454543). Rules are 2px black.

### Named Rules
**The Readable Accent Rule.** Never set text in raw `--accent`. Text uses `--accent-ink` on the ground or `--accent-fg` on an accent fill. `--accent-ink` is computed to clear 4.5:1 against both the preset's ground and its surface.

**The No Muted On Brand Rule.** On accent-filled sections (and the clean-local band, which is the accent), secondary text uses the full `--accent-fg`. A mid-tone brand colour leaves no contrast headroom for a muted shade; hierarchy comes from size and weight instead.

**The Neutral Surface Rule.** Surfaces, cards and rules are greys derived from the preset's own ground (shifted toward black on light presets, toward white on industrial). They never carry a hue of their own: no blue-grey "tech" plates. The brand accent is the only colour on the page.

**The Display Face Rule.** `--font-display` sets headings and big numbers (the phone, rating and step numerals), plus the logo and the display-size town list. Paragraphs, quotes, labels, buttons, links and form text always use `--font-body`. globals.css enforces this with a guard rule.

**The One Brand Rule.** No second brand colour, no gradients between colours. Depth comes from the preset's neutrals.

## Typography

| Preset | Display | Body | Character |
|---|---|---|---|
| heritage | Brygada 1918 600 | Libre Franklin 400/500 | Early-20th-century book serif with a working-sans partner: the painted fascia and the invoice. |
| industrial | Big Shoulders Display 800, uppercase | Barlow 400/500/600 | Condensed signage cut and a road-sign grotesque: site hoarding, spec sheets. |
| clean-local | Bricolage Grotesque 700 | Figtree 400/600 | Warm, slightly quirky grotesque that's friendly without being childish. |
| bold | Epilogue 800, tight | Hanken Grotesk 400/600 | Heavy, compact display for van-livery scale; a crisp neutral body. |

### Hierarchy (tokens, shared names)
- **Display** (`--step-5`, `clamp(2.6rem, 7.4vw, 5.6rem)` in bold, smaller in heritage): hero headline only.
- **Headline** (`--step-4`): section headings.
- **Title** (`--step-2`): service names, step titles.
- **Body** (`--step-0`, 1.0625rem, line-height 1.55 to 1.65, max 65ch).
- **Label** (`--step--1`, 600, tracked +0.06em uppercase in industrial and bold, sentence case in heritage and clean-local): form labels, review metadata, footer headings. Never a kicker above a heading, and never above the phone number.
- **Small** (`--step-small`, 0.9375rem) and **Fine** (`--step--2`, 0.8125rem): secondary lines, captions and legal text. These are the only sizes below body; no one-off `text-[…]` sizes.

### Named Rules
**The Phone Is Type Rule.** Wherever the layout allows, the phone number is set in the display face at headline size, with tabular figures.

## Layout

- **Container:** `--maxw` (1200px) with `--gutter` (16px on a 390px phone, up to 40px).
- **Section rhythm:** each preset sets `--section-y`. Heritage breathes, industrial is compact, bold is loud and airy.
- **Mobile first:** single column below 768px. Grids move to 2 or 3 columns at `md`/`lg`. A 64px sticky Call / WhatsApp bar sits on phones, and the page reserves space for it.
- **Tones:** every section sits on one of four tones: `base`, `surface`, `band` (dark or brand) or `accent`. `sections.json` can override a variant's default tone, so the page alternates rhythm deliberately.

## Elevation & Depth

Flat by default. Depth comes from tone changes between sections and 1px (bold: 2px) rules. The only shadow is the sticky call bar's lift (`0 -8px 24px -12px rgb(0 0 0 / .35)`) and the clean-local hero image (`0 24px 48px -24px rgb(0 0 0 / .25)`).

## Shapes

| Preset | Radius | Buttons | Borders |
|---|---|---|---|
| heritage | 3px / 6px | 3px, 1px outline secondary | hairline rules, double rule under the nav |
| industrial | 0 / 2px | square | 1px seams, grid lines |
| clean-local | 14px / 24px | pill | soft 1px |
| bold | 0 | square, 2px border | 2px black |

## Components

- **Buttons:** `.btn-primary` is an accent fill with `--accent-fg`. `.btn-secondary` is outlined in `--text` (on band tones, `--band-text`). The minimum height is 48px (52px on hero).
- **Coverage line:** a pin icon in `--accent-ink` followed by town names joined by middots. It appears in heroes and the service area.
- **Sticky call bar (mobile):** two equal halves, Call (accent fill) and WhatsApp (surface, only when the number is a mobile). If there's no phone, the bar becomes a single "Get a quote" link.
- **Review:** stars in accent-ink with the text as body, and the author as a label with a "Google review" source. It only renders from real review data. The overall rating appears once near the top: the hero proof line, or trust-rating, never both.
- **Lists instead of icon cards:** services and trust promises are ruled lists and spec-sheet rows (title + one line). `services-list-icons` is the single icon-led variant. There are no icon-tile card grids.
- **Photos:** a real Google Places photo (best landscape at least 1200px) always gets an image hero, and a second one goes in About. Every Places photo shows its "Photo: … on Google" credit (a Google requirement). With no photo, the typographic hero draws the trade's icon as an oversized hairline outline in the brand colour (`.hero-mark`, 9–12% opacity) so the first screen is never an empty wash.
- **One container:** every section's content starts on the nav logo's left edge (`.wrap`). There are no centred or offset content columns; the centred-logo nav centres the name on the header's own centre line.
- **Hero quote:** at most 25 words with an ellipsis, taken from the review whose first sentence stands alone (`hero.quote`, chosen at build).
- **Tap targets:** every standalone link is at least 44px tall on phones (nav, footer, contact details, `.link`).
- **The page ends once:** one phone moment at the close (a CTA band, contact details *or* the big-phone footer), never two in a row. `catalogue.json` rules and `site_library.normalize_sections` enforce this.

## Do's and Don'ts

- **Do** name towns, the county and the owner's first name in copy.
- **Do** render nothing (not an empty box) when optional data is missing.
- **Do** keep every text node mapped to a `content.json` key via `data-edit`.
- **Don't** add kickers or eyebrows, gradient text, glass, icon-tile card grids, fake stats or invented credentials.
- **Don't** hardcode hex colours in sections; use the tokens.

## Labs variants (opt-in)

Seven variants built from the Dribbble study in `INSPIRATION.md` are marked `"labs": true` in `catalogue.json`. SiteForge only offers them to the composer when `SITEFORGE_LABS=1`; otherwise any labs id is swapped for its stable twin (`site_library.LABS_STABLE`).

| Variant | Slot | Idea | Reference |
|---|---|---|---|
| `hero-editorial` | hero | Photo under visible hairline grid columns; services on a rule; phone card in the bottom-right cell | R2, R7 |
| `hero-colour-field` | hero | The accent drenches the hero, darkened only toward the empty top-right corner; services as a ruled label row | R4 |
| `hero-quick-quote` | hero | "What needs doing?" box with service chips that prefills the quote form; big phone beside it | R3 (interaction only) |
| `services-index` | services | One bordered table of shared hairlines; each cell starts a quote for that service | R6 |
| `area-marquee` | service-area | One slow loop of town names (3+ towns); pauses on hover, a still wrapped list under reduced motion | R1 |
| `footer-wordmark` | footer | The name measured to span the container, cropped by the bottom edge; wraps when a long name would get too small | R5, R2 |
| `contact-chips` | contact | Quote form that opens with tappable service chips | R6, R3 |

**Labs rules:** the quick-quote hero and the services index need a form contact (SiteForge swaps `contact-details` for `contact-form-split`). In clean-local the band *is* the accent, so band and accent count as one colour in the tone rhythm. "+" marks (`GridMark`) are decoration only and never sit in the text flow, so they don't shift the left edge.
