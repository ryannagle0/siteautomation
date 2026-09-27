# Cloud handoff: section library (`cloud/section-library`)

Build Site no longer clones one template (`derek-doyle-electrical`, now removed). It composes each site from a **section library**: one of 4 style presets plus one of 37 section variants per slot. The copy is written by Claude around real facts about the business, and a check strips invented claims (years, registrations, insurance, prices).

## What changed

### New: `sites/_library/` (Next.js 14 + TypeScript + Tailwind)

**Design context (Impeccable):**
- `PRODUCT.md`
- `DESIGN.md`: 4 presets, each with its own fonts, type scale, spacing, radius and colour roles:
  - **heritage:** Brygada 1918 + Libre Franklin
  - **industrial:** Big Shoulders Display + Barlow
  - **clean-local:** Bricolage Grotesque + Figtree
  - **bold:** Epilogue + Hanken Grotesk
- `.impeccable/surfaces/…`: the direction contract

**Where things live:**
- **Copy:** all text is in `src/content.json`, with no copy hardcoded in components. Interface strings sit in `content.ui`, with defaults in `ui-defaults.json`.
- **Composition:** `src/sections.json` sets section order, variant and tone. `src/site.json` holds the preset, slug and beacon URL.
- **Tokens:** all design tokens are CSS variables in `src/tokens.css`. The `SITE:BEGIN…END` block holds the brand accent. SiteForge computes `--accent-fg` and a contrast-safe `--accent-ink` for every preset.
- **Editing hooks:** every section root has `data-slot`, and every text node has `data-edit="<content.json path>"`.

**37 variants** in `src/components/sections/<slot>/`:

| Slot | Variants |
|---|---|
| nav | minimal, centred-logo, phone-bar |
| hero | split-image, full-bleed, typographic, image-grid, review-led |
| trust | strip, grid, rating |
| services | grid, list-icons, featured-grid, tabs |
| about | split, owner-note, facts |
| process | steps, timeline, cards |
| reviews | featured, grid, carousel (real reviews only) |
| gallery | grid, mosaic (3+ real photos only) |
| service-area | towns, map |
| cta | band, split, callout |
| contact | form-split, details, form-centered |
| footer | simple, columns, big-phone |

**Shared behaviour:**
- **Missing data:** every variant renders nothing, or a designed fallback, when its data is missing (no photos, no email, no reviews).
- **Mobile:** a sticky Call / WhatsApp bar on phones. WhatsApp only appears for mobile numbers.

**Kept and carried over:**
- BrandMark and `brand.json`
- EditBridge, which now sends the `data-edit` path so inline edits write straight to `content.json`
- The favicon and OG image written by `logos.py`
- MorphingSquare, used as the form's sending state
- The map, now lazy-loaded so pages without it skip ~200 kB of JS

**New components and tools:**
- **ViewBeacon:** when a prospect opens a deployed demo, the site pings SiteForge.
- **`catalogue.json`:** every variant with its slot, a one-line description, needs, optional fields, best presets and default tone, plus composition rules. It is sent minified to the AI on each build.
- **Samples and QA:** `samples/<preset>/` holds 4 synthetic sample businesses; switch between them with `npm run sample -- <preset>`. `/catalogue?preset=…` renders every variant in one preset for QA (removed from built sites).

### New: `site_library.py`
- **Composition:** `compose()` asks Claude (Haiku) for a preset, sections and copy. `normalize_sections()` then enforces the catalogue and data rules:
  - no reviews or gallery sections without real data
  - no hero that needs photos when there are none
  - no back-to-back band tones
  - one phone moment at the end of the page
  - the rating shown once
- **Copy checks:** `sanitize_content()` strips unverifiable claims, and the hero headline must name the town. Without an API key, or if the AI call fails, a plain, true fallback copy is used.
- **Photos:** `scene_images()` generates 2 Gemini photos (hero and about). Each is checked by Claude vision and kept only if it scores 7/10 or higher with no text, logos or warped hands. Results are cached per lead in `data/images/`, so rebuilds cost nothing.
- **Shared `node_modules`:** `link_node_modules()` / `detach_node_modules()` link each site's `node_modules` to the library's: a **junction on Windows** (`_winapi.CreateJunction`, falling back to `mklink /J`) and a symlink elsewhere. Deleting a site removes the link first and never the shared install.

### `app.py`
- **Build Site:**
  1. Gathers facts: the Place Details call (rating, up to 5 real Google reviews, opening hours, location) and the nearest towns from `data/ireland_counties.json`.
  2. Generates photos (optional).
  3. Composes the site and writes `content.json`, `sections.json`, `site.json`, `tokens.css`, `fonts.ts` and `brand.json`.
  4. Links `node_modules` and starts the preview.
- **Edits on library sites:**
  - **Edit Site / hotbar:** section-scoped edits resolve the variant file through `sections.json`.
  - **Claude's instructions:** Claude gets library-specific guidance (copy in `content.json`, colours via tokens), and invalid JSON is never written.
  - **Allowed packages:** the list comes from each site's `package.json`, so `framer-motion` is no longer offered to library sites.
  - **Inline text edits:** they write straight to the `content.json` key. Editing the phone updates tel/WhatsApp too, and editing the name updates `brand.json` too.
  - **21st.dev swaps:** they target the slot's variant file.
- **Theme panel:** on library sites, "Font" becomes **Style** (the 4 presets). Accent and corners write the `SITE` block.
- **Pipeline:** new lead fields `preset`, `views` and `last_viewed`, and a new `POST /api/beacon/<slug>` route. The pipeline shows **Demo views** and **Style**.
- **Deploy:** now walks the site folder without descending into `node_modules`.
- **Older sites:** sites built from the old template keep working. Every changed path checks `is_library_site()` first and falls back to the old behaviour. The Windows process handling (taskkill, netstat, `npm.cmd`) and the `.vbs`/`.bat` launchers are unchanged.

### Other files
- **`templates/index.html`:** forwards the `data-edit` path, adds the Style label, and shows views and preset in the pipeline.
- **`logos.py`:** preset font names added to the emblem font map.
- **`.gitignore` / `.dockerignore`:** now keep `sites/_library/` (minus its `node_modules`, `.next` and review screenshots), and ignore `data/images/`.
- **`Dockerfile`:** runs `npm ci` in `sites/_library` once.
- **`.claude/skills/impeccable`:** the Impeccable skill, committed so it persists. Its auto-run detector hooks were deliberately not installed.

## Quality pass (Impeccable)
- **Screenshots:** each preset's sample page was captured at 390px and 1440px.
- **Automated audit:** checked WCAG contrast against the real painted background, 44px tap targets, one h1, heading order, form labels and alt text. It passes on all 4 samples and on every variant in every preset. The fixes this round needed:
  - accent ink is now checked against the preset's surface as well as its ground
  - no muted text on brand-colour sections
  - larger tap targets on phones
- **Detector:** `impeccable detect` found no real issues. Its 12 "broken-image" warnings are false positives from the `<Img>` wrapper. Off-scale font sizes were moved onto type tokens.
- **Finish review** (fresh reviewer agent: critique, then polish verdict):
  - **First verdict: fix.** It raised icon-card grids, headlines missing the town, bare stars, stacked phone endings, a "CALL" eyebrow and mobile name truncation.
  - **Second pass:** 7 of 8 fixes were resolved and 1 was partial (repeated contact details in the industrial sample's ending).
  - **Final state:** that last fix was applied and recaptured, but not sent for a third review, because Impeccable caps these at two rounds.
- **Known ceilings the reviewer noted, left for later:** the map/coverage motif could go further (currently a pin plus towns at display size), and the hero has only one small load motion.
- **Concept roll:** ran in degraded mode (its service was unreachable from the cloud). Your brief pinned the presets anyway.

## Not tested here (no keys, no Windows, no outbound access to these hosts)
1. **Windows junction linking.** Only the Linux symlink path was exercised: build, rebuild and delete all worked, and the shared install survived. **Check this first.**
2. **Live Claude composition.** It was tested with a fake client that deliberately broke rules; validation and sanitising handled it.
3. **Live Gemini generation and Claude image QA.** Tested with mocks. The default model is `gemini-2.5-flash-image`; override it with `GEMINI_IMAGE_MODEL`.
4. **Live Place Details** (reviews, hours, location). Mocked. **This is a paid Enterprise + Atmosphere call**, made once per lead per 30 days (cached).
5. **Vercel deploy of a library site.** The file list was verified: 82 files, no `node_modules`. A composed site builds with `next build`.
6. **Other live services:** map tiles, Resend email and the dashboard clicked through in a browser. Photo stand-ins were used for screenshots.

## Run this on Windows after pulling
1. Get the branch:
   ```powershell
   git fetch origin
   git checkout cloud/section-library
   ```
   Or merge the PR, then `git pull` on master.
2. Install the library's dependencies once (every built site shares them):
   ```powershell
   cd sites\_library
   npm ci
   cd ..\..
   ```
3. Python: there are no new packages. If in doubt, run `pip install -r requirements.txt`.
4. Add to `.env` (all optional):
   ```
   GEMINI_API_KEY=your-key          # scene photos; without it sites build without photos
   GEMINI_IMAGE_MODEL=gemini-2.5-flash-image
   SITEFORGE_PUBLIC_URL=            # e.g. your Railway URL; turns on demo view tracking
   SHARED_NODE_MODULES=1            # set to 0 to go back to one npm install per site
   ```
5. Restart SiteForge: run `stop_siteforge.bat`, then `start_siteforge.vbs`.
6. Test: in Pipeline, click **Rebuild** on one lead and check the preview. Then open **Edit Site** and:
   - double-click a heading
   - try the theme panel's **Style** chips
   - click **Deploy**
7. If the build fails at the node_modules step: check that `sites\<slug>\node_modules` shows as a junction (`dir` lists `<JUNCTION>`). If it's still broken, set `SHARED_NODE_MODULES=0` in `.env` and restart.
8. On Railway: add `GEMINI_API_KEY` and `SITEFORGE_PUBLIC_URL` to the service variables. The Dockerfile installs the library's dependencies itself.
9. Existing demo sites still work as they are. Rebuild a lead to move it onto the library. Rebuilding replaces that site's whole folder, **including its undo history** (this was already how Rebuild worked), so deploy first any site whose current version you want to keep live.
