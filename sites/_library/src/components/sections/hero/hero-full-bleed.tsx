import { HeroProof } from "@/components/HeroProof";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, Coverage } from "@/components/parts";
import { asset, content, hasImage } from "@/lib/content";
import { cn } from "@/lib/cn";

/**
 * Photo across the full width with the words set low on a scrim. Without a
 * photo it becomes a band-tone field: the same composition, type doing the work.
 */
export default function HeroFullBleed({ tone = "band" }: { tone?: Tone }) {
  const hero = content.hero;
  if (!hero) return null;
  const img = hasImage(hero.image) ? hero.image : null;
  return (
    <Section slot="hero" tone={img ? "band" : tone} className="relative isolate overflow-hidden">
      {img && (
        <>
          <img src={asset(img.src)} alt={img.alt || ""} width={img.width} height={img.height} fetchPriority="high"
            className="absolute inset-0 -z-20 h-full w-full object-cover" />
          {/* Legibility scrim: darkest where the text sits. */}
          <div aria-hidden="true" className="absolute inset-0 -z-10"
            style={{ background: "linear-gradient(to top, rgb(0 0 0 / 0.82) 0%, rgb(0 0 0 / 0.55) 45%, rgb(0 0 0 / 0.15) 100%)" }} />
        </>
      )}
      <div className={cn("wrap flex flex-col justify-end", img ? "min-h-[min(88svh,760px)] pb-12 pt-40 md:pb-20" : "py-20 md:py-28")}
        style={img ? { ["--text" as string]: "#fff", ["--muted" as string]: "rgb(255 255 255 / 0.82)", ["--accent-ink" as string]: "#fff" } : undefined}>
        <div className="hero-rise max-w-4xl">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-5 max-w-2xl" />
          <Coverage className="mt-6 text-step-small" />
          <Actions slot="hero" whatsapp className="mt-8" />
          <HeroProof className="mt-7" />
        </div>
      </div>
    </Section>
  );
}
