# SiteForge section library

The Next.js 14 app every SiteForge demo site is composed from. SiteForge copies it for each lead, then writes:

- **`src/content.json`:** every word on the page. Components read it through `<T k="path" />`, which also tags the element `data-edit="path"` for inline editing.
- **`src/sections.json`:** the ordered sections, as `[{ "slot", "variant", "tone"? }]`.
- **`src/site.json`:** the style preset (`heritage`, `industrial`, `clean-local` or `bold`), the slug and the view-beacon URL.
- **`src/tokens.css`:** the `SITE:BEGIN … SITE:END` block holding the brand accent and its contrast-safe companions.
- **`src/fonts.ts`:** only the chosen preset's two fonts.
- **`src/brand.json`:** the logo mode and emblem.

## Files

| Path | What it is |
|---|---|
| `src/components/sections/<slot>/<variant>.tsx` | 37 section variants, registered in `registry.ts` |
| `catalogue.json` | Compact description of every variant, sent to the AI composer on each build |
| `DESIGN.md`, `PRODUCT.md`, `.impeccable/` | Design system and product context (Impeccable) |
| `samples/<preset>/` | Four synthetic sample businesses for design QA. Never shipped. |
| `ui-defaults.json` | Default interface strings (button labels, form messages), merged into `content.ui` |

## Working on the library

```bash
npm install
npm run sample -- heritage     # or industrial | clean-local | bold
npm run dev                    # http://localhost:3000
                               # http://localhost:3000/catalogue?preset=bold shows every variant
npm run build
```

`npm run sample` copies a sample into `src/` and writes its accent. Put stand-in photos in `public/_samples/`; that folder is git-ignored.

## Adding a variant

1. Create `src/components/sections/<slot>/<id>.tsx`. Its root must be `<Section slot="<slot>" tone={tone}>`, all copy must come through `<T k=…/>` or `ui()`, and it should return `null` when its data is missing.
2. Register it in `src/components/sections/registry.ts`.
3. Describe it in `catalogue.json` (`id`, `slot`, `desc`, `needs`, `optional`, `best`, `tone`).
4. Check it at `/catalogue?preset=…` in all four presets, at 390px and 1440px.

Built sites share this folder's `node_modules`: SiteForge links to it with a junction on Windows and a symlink elsewhere.
