# Cloud handoff: design fixes (`cloud/design-fixes`)

Ten fixes to the section library, the build pipeline and the editor, in seven groups. After each group I audited all 4 sample pages and every variant in every preset at 390px and 1440px:
- **Contrast:** checked against the real background.
- **Tap targets:** at least 44px.
- **Alignment and fonts:** two checks added this round (content aligned to the logo's edge, display font only on headings and big numbers).
- **Rating count:** a new check that the rating value appears at most twice per page.
- **Detector:** `impeccable detect`.

Everything passes.

## What changed

### 1. Photos (`site_library.py`, `app.py`, hero/about variants)
- **Photo source:** Place Details now also requests `photos`. `places_photos()` downloads the lead's **own Google photos**, taking the best landscape photo at least 1200px wide for the hero and a second one for About. Claude vision rejects logos, flyers, screenshots and blurry shots. Choices are cached per lead in `data/images/`.
- **Attribution:** the photographer credit ("Photo: … on Google", which Google requires) is shown on the photo.
- **Gemini:** now only fills a slot that has no Places photo.
- **Layout rules:** a hero photo **forces** an image hero (split-image, or full-bleed in industrial/bold). No hero photo forces the typographic hero (or review-led when reviews exist). A second photo switches About to a variant that shows it.
- **No photos:** `hero-typographic` draws the trade's icon (zap, droplets, leaf…, set in `hero.icon`) as an oversized hairline outline in the brand colour at 9–12% opacity.

### 2. Alignment
Every section's content now starts on the nav logo's left edge. The fixes:
- **`nav-centred-logo`:** the name drifted off-centre when the text beside it was long, because the browser sized its grid column to the longest single word. It's now centred on the header's own centre line. This is the likely cause of the offset look on Accell Electrical.
- **`process-cards` and `contact-form-centered`:** these were centred columns; they now start on the left edge. The ids are kept so existing sites still work.

### 3–4. Rating and hero quote
- **Rating:** it now shows at most twice per page, once in the hero and once in the reviews section:
  - `hero-review-led` shows only the review card, with no separate badge.
  - Trust items and about-facts that mention the rating are dropped, and the AI is told to use area, hours or contact facts instead.
- **Hero quote:** chosen at build time (`hero.quote`) from the review whose first sentence stands alone, skipping openings like "He was great…", and cut to 25 words with an ellipsis.

### 5–6. Typography and surfaces
- **Display font:** used only for headings, big numbers, the logo and the town list. It was removed from the trust titles, review quotes and the owner signature. A guard rule in `globals.css` forces the body font on paragraphs, quotes, labels, buttons, links and form text whatever class is applied.
- **Neutral surfaces:** every preset's surfaces now derive from its own background. Industrial is true neutral charcoal (#101010 / #1C1C1C / #262626 / #333333), with no blue cast. The contrast inputs in Python and in the sample script were updated to match.

### 7. Logo check (`logos.py`, `app.py`)
- **Vision check:** now runs on every detected emblem and returns `generic_symbol` (recycling arrows, globe, tick, swoosh, clip-art house or bolt…) and its own `confidence`.
- **Suspect logos:** a stock symbol or confidence under 0.6 marks the logo as suspect. The site then uses the initials monogram (`gen:1`), and the pipeline card shows **"Logo: check"**. Picking "extracted" in the logo editor still overrides this.

### 8. Editor overlay (`templates/index.html`, `EditBridge.tsx`)
- **Fade:** the dark fade behind the hotbar is now at most 120px tall and much lighter.
- **Hide button:** a new eye button in the toolbar hides the hotbar entirely, and **H** toggles it. H also works while the preview has focus (EditBridge forwards it). A small "Show editor bar" pill brings it back.
- **Dashboard contrast:** while auditing, I fixed some pre-existing issues. White text on the light blue (3.2:1) now uses a darker fill, muted-label buttons no longer turn blue on hover, and the placeholder and log header are more legible.

### 9. 21st.dev curation
- **Hidden results:** anything whose name or description mentions AI, SaaS, startup, app, dashboard, pricing plan, crypto or developer.
- **New "Local business" chip (on by default):** it ranks service, contact, testimonial/review, gallery, map/location, booking, footer, CTA and quote components first. When you're browsing "All", it also searches with local-business terms.

### 10. Claim guard (`site_library.claim_guard`)
- **What it checks:** before `content.json` is written, any 24-hour/24-7, emergency, years-in-business or certification claim (Safe Electric, RECI, RGII, SEAI, registered, insured…) must appear in the source data: the business name, trade, real review text, Google opening hours, or the lead's `years` field.
- **What happens otherwise:** the sentence is removed, and a list item that loses its title goes entirely.
- **Logging:** every removal is logged in the server log, returned as `claims_removed` from Build Site, and shown in the dashboard's Recent actions.
- **Always removed:** prices, superlatives, guarantees and fake urgency, whatever the data says.

## Tested here
- **End-to-end Build Site:** a fake Claude plus mocked Google responses (photos, reviews, hours) on an Accell-style lead. It produced the photo hero and About photo with credits, the trimmed quote, dropped the rating repeats, and removed 3 claims.
- **Unit tests:** the logo suspect logic and the claim guard.
- **Dashboard in a real browser:** hotbar toggle, H key, the 120px fade and the drawer filtering/ranking.
- **Last round's route tests:** still pass. They also caught one guard bug, fixed.
- **Builds:** `npm run build` in `sites/_library` passes, and `py_compile` passes.

## Not tested here
- **Live Google, Claude and Gemini calls.** The Places photo download is a paid call per downloaded photo (usually 1–4 per lead, cached 30 days). Place Details now also requests `photos`.
- **Windows.** Nothing Windows-specific changed this round.
- **Real 21st.dev results.** The filter and ranking were only tested on mock results.

## Dribbble inspiration task: not started
Your images are at `C:\Users\ryana\OneDrive\Documents\inspiration` on your PC, which a cloud session can't read. To run that task, copy the folder into the repo as `sites\_library\inspiration\` and push it, as described below.

## Run this on Windows after pulling
1. Get the branch:
   ```powershell
   git fetch origin
   git checkout cloud/design-fixes
   ```
   Or merge the PR, then `git checkout master` and `git pull`.
2. `cd sites\_library`, then `npm ci`, then `cd ..\..`. Dependencies are unchanged; this just keeps your shared install in step.
3. There are no new Python packages and no new `.env` keys. The Places photos use your existing `GOOGLE_MAPS_API_KEY`.
4. Restart SiteForge: run `stop_siteforge.bat`, then `start_siteforge.vbs`.
5. Test:
   - Click **Rebuild** on Accell Electrical and on a lead with no photos.
   - In the editor, press **H**.
   - Open the component drawer and check the Local business chip.
   - Check Recent actions for "Claim guard" lines.
6. For the Dribbble task, after merging this PR, run:
   ```powershell
   git checkout master
   git pull
   Copy-Item -Recurse "C:\Users\ryana\OneDrive\Documents\inspiration" sites\_library\inspiration
   git add sites/_library/inspiration
   git commit -m "Add Dribbble inspiration images"
   git push
   ```
