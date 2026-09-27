// Library development only: `npm run sample -- heritage` copies a sample
// business from samples/<name>/ into src/ and writes its accent into the
// SITE block of src/tokens.css — the same thing SiteForge's app.py does for
// a real lead (see site_accent_block() there; keep the two in step).
import { readFileSync, writeFileSync, copyFileSync, existsSync } from "node:fs";
import { join } from "node:path";

const name = process.argv[2];
// `npm run sample -- bold labs` uses samples/<name>/sections.labs.json instead
// (any second word works the same way: sections.<word>.json).
const labs = process.argv[3] || "";
const dir = join("samples", name || "");
if (!name || !existsSync(dir)) {
  console.error("usage: npm run sample -- <heritage|industrial|clean-local|bold> [labs]");
  process.exit(1);
}
for (const f of ["site.json", "brand.json"]) copyFileSync(join(dir, f), join("src", f));
copyFileSync(join(dir, labs ? `sections.${labs}.json` : "sections.json"), join("src", "sections.json"));
// content.json gets the library's default interface strings (content.ui) merged under its own.
const sampleContent = JSON.parse(readFileSync(join(dir, "content.json"), "utf8"));
const uiDefaults = JSON.parse(readFileSync("ui-defaults.json", "utf8"));
sampleContent.ui = { ...uiDefaults, ...(sampleContent.ui || {}) };
writeFileSync(join("src", "content.json"), JSON.stringify(sampleContent, null, 2) + "\n");

// accent-ink must read on each preset's ground AND its surface tone.
const PRESET_BG = { heritage: ["#f2f0eb", "#e7e5e1"], industrial: ["#101010", "#262626"], "clean-local": ["#ffffff", "#eaeaea"], bold: ["#ffffff", "#e3e3e3"] };
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const toHex = (rgb) => "#" + rgb.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0")).join("");
const lum = (h) => {
  const [r, g, b] = hex(h).map((v) => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const contrast = (a, b) => {
  const [x, y] = [lum(a), lum(b)].sort((m, n) => n - m);
  return (x + 0.05) / (y + 0.05);
};
const mix = (a, b, t) => toHex(hex(a).map((v, i) => v + (hex(b)[i] - v) * t));
const ink = (accent, grounds) => {
  const target = lum(grounds[0]) > 0.5 ? "#000000" : "#ffffff";
  for (let t = 0; t <= 1; t += 0.04) {
    const c = mix(accent, target, t);
    if (grounds.every((g) => contrast(c, g) >= 4.5)) return c;
  }
  return target;
};

const accent = readFileSync(join(dir, "accent.txt"), "utf8").trim().toLowerCase();
const fg = contrast(accent, "#ffffff") >= contrast(accent, "#111111") ? "#ffffff" : "#111111";
const block = [
  "/* SITE:BEGIN — written by SiteForge (brand colour + contrast companions). */",
  ":root {",
  `  --accent: ${accent};`,
  `  --accent-fg: ${fg};`,
  "}",
  ...Object.entries(PRESET_BG).map(([p, bg]) => `[data-preset="${p}"] { --accent-ink: ${ink(accent, bg)}; }`),
  "/* SITE:END */",
].join("\n");
const tokens = readFileSync("src/tokens.css", "utf8");
writeFileSync("src/tokens.css", tokens.replace(/\/\* SITE:BEGIN[\s\S]*?SITE:END \*\//, block));
console.log(`sample "${name}"${labs ? ` (${labs})` : ""} in place (accent ${accent}, fg ${fg})`);
