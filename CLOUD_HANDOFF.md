# Cloud handoff: Dribbble-inspired labs variants (`cloud/inspiration`)

Seven new section variants based on the patterns in your 7 Dribbble references (analysed in `sites/_library/INSPIRATION.md`). They're built to be **fully reversible**: they're "labs" variants, **off by default**, and no existing variant was changed.

## How to turn it on, or back off
- **Try it:** add `SITEFORGE_LABS=1` to `.env`, restart SiteForge, then Build Site or Rebuild a lead. The composer can now pick the new variants.
- **Don't like it:** remove the line (or set it to `0`) and restart. New builds go back to the stable library exactly as before. Existing sites that already use a labs variant keep rendering, because the code stays in the library.
- **Remove it completely:** close this PR without merging. If it's already merged, `git revert` the merge commit. The branch `backup/pre-inspiration` points at master before any of this work (`e6dad0f`).

## What changed

### New variants (`sites/_library/src/components/sections/…`, each marked `"labs": true` in `catalogue.json`)
| Variant | What it is | Inspired by |
|---|---|---|
| `hero/hero-editorial` | Full-bleed photo under visible hairline grid columns, a poster headline, the top services on a rule, and a phone card in the bottom-right cell. Without a photo it's the same grid on the band tone. | R2 Longbow grid, R7 Kensho label row |
| `hero/hero-colour-field` | The brand colour fills the hero, with depth from a single hue and "+" registration marks. The services run as a ruled label row near the bottom. | R4 Tech Recruit colourways |
| `hero/hero-quick-quote` | The hero is the start of the quote: a "What needs doing?" box with service chips. Pressing send scrolls to the contact form and **prefills** it. A big "Or ring" phone number sits beside it. | R3 (the input-as-focal-point idea only) |
| `services/services-index` | Services as one bordered table with shared hairlines. Tapping a cell opens the quote form with that service picked. | R6 services table |
| `service-area/area-marquee` | A slow loop of town names at headline size. It pauses on hover and becomes a still, wrapped list under reduced motion. Needs 3+ towns. | R1 marquee band |
| `footer/footer-wordmark` | Phone, email and links, then the business name at poster size, cropped by the bottom edge. The name is measured so it spans exactly, whatever its length or the font; a very long name wraps instead of shrinking to fine print. | R5 cropped poster word, R2 |
| `contact/contact-chips` | A dark closing contact section. The form opens with tappable service chips instead of a dropdown. | R6 chip form, R3 |

### Supporting code
- **New components:** `FitWord.tsx`, `GridMark.tsx` ("+" mark), `QuickQuote.tsx` and `ServiceCell.tsx`.
- **`ContactForm.tsx`:** now accepts a prefill event (`requestQuote`) and has an optional `chips` mode. Existing forms look and behave the same, apart from focusing the Name field after a prefill.
- **Other library files:**
  - `globals.css`: marquee styles.
  - `ui-defaults.json`: six new interface strings.
  - `registry.ts`: 44 variants.
  - `DESIGN.md`: a new labs section.
- **`site_library.py`:**
  - `labs_enabled()`, with a `LABS_STABLE` swap map.
  - Labs variants are left out of the AI prompt unless labs are on.
  - The data rules: area-marquee needs 3+ towns. The quick-quote hero and services-index force a form contact. hero-editorial counts as a photo hero.
- **`app.py`:** the AI "edit" guidance only lists labs variant ids when labs are on.
- **Samples:** `samples/<preset>/sections.labs.json`, plus `npm run sample -- bold labs` to preview a labs page in the library.
- **One shared-behaviour change (small):** in clean-local, the band tone *is* the accent colour. The tone-rhythm check now counts band and accent as the same colour, so two green sections can't sit back to back. This applies with labs off too; it only prevents a clash.

### Existing variants
**None changed.** The refinements from the plan (a grid overlay on `hero-full-bleed`, "+" marks on `process-steps`, arrows on the carousel) went into the new variants instead, to keep the stable library untouched.

## Quality pass (done here)
- **Screenshots:** all four labs sample pages (heritage, industrial, clean-local, bold) at 390px and 1440px, plus a stress page: a 57-character name, no phone, no email, no hours, one service, two towns, no subhead, no service chips.
- **Audit script:** checks contrast on the real background, 44px tap targets, alignment with the logo edge, display font on small text, and rating count. Everything is clean except one expected result: the chip radio inputs are visually hidden, and their 44px labels are the tap target.
- **`impeccable detect`:** 0 anti-patterns.
- **Fixed during critique and polish:**
  - A "+" mark pushed the colour-field headline off the left edge.
  - The services table had uneven title heights and a ragged last row (the last cell now spans the gap).
  - The marquee didn't wrap under reduced motion.
  - The footer name overflowed for long names.
  - A footer measurement bug under reduced motion (the global 0.01ms transition).
  - The phone in the quick-quote hero overflowed.
  - The selected chip was invisible on the green band.
  - The colour-field gradient could lower text contrast (it now only darkens the empty corner).
  - The grid line crossed the hero text on phones.
  - Phone links were under 44px.
  - The footer nav drifted right when there's no phone or email.
- **Builds:** `npm run build` passes, and `py_compile` passes for `app.py` and `site_library.py`. The labs gating has unit checks with labs on and off.

## Not tested here
- **Windows:** nothing Windows-specific changed.
- **Live Claude composition with labs on:** the gating and swap rules were tested with fixed inputs, not a real Haiku call.
- **Real brand colours:** the colour-field hero was checked with the four sample accents. A very pale accent still gets a dark `--accent-fg`, so text stays readable.

## Spotted, not fixed (an existing variant)
- **`nav-centred-logo` at 390px:** with a long business name, the phone number in the top-right wraps onto three lines. I left it alone because this task doesn't change stable variants.

## Run this on Windows after pulling
1. Get the branch:
   ```powershell
   git fetch origin
   git checkout cloud/inspiration
   ```
2. Update the library's install:
   ```powershell
   cd sites\_library
   npm ci
   cd ..\..
   ```
   Dependencies are unchanged.
3. Optional, to preview the new variants in the library on their own:
   ```powershell
   cd sites\_library
   npm run sample -- bold labs
   npm run dev
   ```
   Then open http://localhost:3000. Try `industrial`, `clean-local` and `heritage` too. Afterwards run `git checkout src` to put the default sample back.
4. To let SiteForge use them, add this line to `.env`:
   ```
   SITEFORGE_LABS=1
   ```
   There are no new Python packages and no other new keys.
5. Restart SiteForge: run `stop_siteforge.bat`, then `start_siteforge.vbs`.
6. Rebuild a lead or two and look at the result. To go back, delete the `.env` line and restart.
