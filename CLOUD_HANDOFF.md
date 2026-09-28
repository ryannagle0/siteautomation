# Cloud handoff: electrician templates (`cloud/electrician-templates`)

Three electrician templates you can put on any site from the dashboard, built from the mockups you picked:
- **#3 Quote Box**, for domestic electricians
- **#8 Van Livery**, for rural electricians or ones with a branded van
- **#4 Spec Sheet**, for commercial electricians

All text is editable in the editor like every other site.

**This branch is built on `cloud/inspiration` (PR #3).** Merging this PR also brings in the labs work from PR #3; the labs variants still only switch on with `SITEFORGE_LABS=1`. If you'd rather keep PR #3 separate, merge PR #3 first and then this one.

## How to use them
1. Build a site as normal, or open one you've already built.
2. Open the theme panel and use the **Style** menu. Below the four usual presets there are three new options:
   - *Template: Quote Box — domestic electricians*
   - *Template: Van Livery — rural / branded van*
   - *Template: Spec Sheet — commercial electricians*
3. Pick one. The fonts, colours **and page layout** change; the copy stays the same.
4. Pick a normal preset to go back. The site's previous layout comes back exactly as it was, and **Undo** works too.
5. The brand colour picker still works: each template recolours to the business's colour.
6. Rebuilding a site that's on a template keeps it on that template. The AI never chooses a template by itself; they're only used when you pick them.

## What changed

### New files
- **Quote Box** (`sites/_library/src/components/sections/`):
  - `nav/nav-quote.tsx`
  - `hero/hero-quote-box.tsx`: a "Tell Tom about the job" box with the services as tap chips. Pressing *Get a price* scrolls to the form with the service and message already filled in. The photo and big "Or just ring" number sit beside it.
  - `process/process-circles.tsx`
- **Van Livery:**
  - `nav/nav-van.tsx`
  - `hero/hero-van.tsx`: the number as the headline, with the raked brand-colour sweep and hi-vis stripe.
  - `service-area/area-band.tsx`
  - `services/services-checklist.tsx`: each line starts a quote.
- **Spec Sheet:**
  - `nav/nav-spec.tsx`
  - `hero/hero-spec.tsx`: the headline highlighter and the covering/hours/rating/phone table. Without a photo, the table runs as a row under the headline.
  - `services/services-spec.tsx`: a ruled table; each cell starts a quote.
- **Shared by all three:** `reviews/reviews-cards.tsx`.
- **Samples:** `samples/tpl-quote-box`, `samples/tpl-van`, `samples/tpl-spec-sheet`.

### Changed files
- **`src/tokens.css`:** three new preset blocks (quote-box, van, spec-sheet), plus accent-contrast lines for them.
- **`src/fonts.ts`:** adds Manrope, Inter and Archivo.
- **`globals.css`:** van sweep, number and stripe styles; spec highlighter; per-template review cards.
- **`ui-defaults.json`:** six new interface strings.
- **`registry.ts`:** now has 55 variants.
- **`catalogue.json`:** 11 entries marked `"template"`, so the AI never uses them on normal sites.
- **`site_library.py`:**
  - New `TEMPLATES`, `STYLES`, `TEMPLATE_SECTIONS`, `template_sections()` and `PRESET_RADIUS`, with fonts and grounds for each template.
  - `set_preset()` now swaps the layout for templates and restores it after.
  - `compose()` keeps a template you picked.
  - Template variants are excluded from the AI prompt and from `normalize_sections`.
- **`app.py`:** the Style menu and validation use `lib.STYLES`, and the corner radius per preset comes from `lib.PRESET_RADIUS`.
- **`scripts/use-sample.mjs`:** contrast grounds for the new presets, and `npm run sample -- <name> <variant>` now accepts any `sections.<variant>.json`.

## Tested here
- **Screenshots and audit:** all three templates at 390px and 1440px with sample data, checked for contrast, 44px tap targets, alignment, overflow and ratings.
- **Missing data:** tested with no phone, no photo, no reviews, one service, one town and a 60-character name. Nothing breaks, and the Spec Sheet hero re-flows without a photo.
- **Editable text:** a check that every piece of business text on each template has a `data-edit` key.
- **Style switching:** tested through the real `/api/theme/<slug>` route (classic → van → classic restores the layout; bad keys give a 400). Unit tests cover template → template, the missing-backup fallback, and `compose` keeping a picked template.
- **Builds:**
  - `npm run build` in `sites/_library` passes.
  - A copied site set to the Van template builds with its own two fonts only.
  - `py_compile` passes for `app.py` and `site_library.py`.
- **`impeccable detect`:** 0 real issues. One flag is a false positive: the van review cards' 6px top stripe, which the detector reads as sitting on a rounded card, but the van rule sets those corners to 0. The advisory font-size notes are for logo sizes and the van number.

## Not tested here
- **Real photos:** the samples use the blurry placeholder images. The templates were designed around the business's own Google photos; the Quote Box and Spec Sheet also look finished without one.
- **The dashboard in a browser on Windows:** the Style menu was tested through the API only. The labels come from `PRESET_LABELS`.
- **Live AI copy on a template:** templates use the same content keys as the rest of the library, so AI-written copy fills them. The small "Tell Tom about the job" label uses `business.ownerFirstName` when there is one.

## Run this on Windows after pulling
1. Get the branch:
   ```powershell
   git fetch origin
   git checkout cloud/electrician-templates
   ```
   Or merge the PR, then `git checkout master` and `git pull`.
2. Update the library's install (dependencies are unchanged; the new fonts come from Google at build time):
   ```powershell
   cd sites\_library
   npm ci
   cd ..\..
   ```
3. There are no new Python packages and no new `.env` keys.
4. Restart SiteForge: run `stop_siteforge.bat`, then `start_siteforge.vbs`.
5. Open a built electrician site, go to Style, and pick one of the three templates.
6. Optional, to preview a template in the library on its own:
   ```powershell
   cd sites\_library
   npm run sample -- tpl-quote-box
   npm run dev
   ```
   You can also use `tpl-van` or `tpl-spec-sheet`. Afterwards run `git checkout src` to put the default sample back.
