import sections from "@/sections.json";
import { SECTIONS, type SectionEntry } from "@/components/sections/registry";
import { MobileCallBar } from "@/components/MobileCallBar";

/**
 * The page is composed from src/sections.json: an ordered list of
 * { slot, variant, tone? }. Unknown variants are skipped (never crash the
 * build); each variant decides for itself whether it has enough content to
 * render. Nav and footer sit outside <main>.
 */
export default function Home() {
  const entries = (sections as SectionEntry[]).filter((s) => SECTIONS[s.variant]);
  const render = (s: SectionEntry, i: number) => {
    const Cmp = SECTIONS[s.variant];
    return <Cmp key={`${s.variant}-${i}`} tone={s.tone} />;
  };
  const nav = entries.filter((s) => s.slot === "nav");
  const footer = entries.filter((s) => s.slot === "footer");
  const body = entries.filter((s) => s.slot !== "nav" && s.slot !== "footer");
  return (
    <>
      {nav.map(render)}
      <main id="top">{body.map(render)}</main>
      {footer.map(render)}
      <MobileCallBar />
    </>
  );
}
