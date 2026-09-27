// LIBRARY ONLY — SiteForge deletes src/app/catalogue when it builds a site.
// Every registered variant, one after another, under the preset given in
// ?preset= (default: site.json's). Used for design QA and screenshots.
import { SECTIONS } from "@/components/sections/registry";
import { siteConfig } from "@/lib/content";

export const dynamic = "force-dynamic";
export const metadata = { robots: { index: false } };

const PRESETS = ["heritage", "industrial", "clean-local", "bold"];

export default function Catalogue({ searchParams }: { searchParams: { preset?: string; slot?: string } }) {
  const preset = PRESETS.includes(searchParams.preset || "") ? searchParams.preset! : siteConfig.preset;
  const ids = Object.keys(SECTIONS).filter((id) => !searchParams.slot || id.startsWith(searchParams.slot));
  return (
    <div data-preset={preset} style={{ background: "var(--bg)", color: "var(--text)" }}>
      {ids.map((id) => {
        const Cmp = SECTIONS[id];
        return (
          <div key={id}>
            <p style={{ font: "600 12px/1 ui-monospace, monospace", padding: "10px 16px", background: "#ff0", color: "#000", margin: 0 }}>
              {id} · {preset}
            </p>
            <Cmp />
          </div>
        );
      })}
    </div>
  );
}
