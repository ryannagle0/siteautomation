import { HeroProof } from "@/components/HeroProof";
import { PhotoCredit } from "@/components/Img";
import { GridMark } from "@/components/GridMark";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, PhoneBig } from "@/components/parts";
import { asset, content, hasImage } from "@/lib/content";
import { cn } from "@/lib/cn";

/**
 * Poster hero on a visible grid (labs). The photo runs full-bleed under
 * hairline column lines; the headline sits low at poster scale, the main
 * services line up on a rule beneath it, and the phone card takes the
 * bottom-right cell. Without a photo it's the same grid on a band tone.
 */
export default function HeroEditorial({ tone = "band" }: { tone?: Tone }) {
  const hero = content.hero;
  if (!hero) return null;
  const img = hasImage(hero.image) ? hero.image : null;
  const services = (content.services?.items || []).filter((s) => s.title).slice(0, 4);
  const onPhoto = img
    ? { ["--text" as string]: "var(--on-scrim)", ["--muted" as string]: "var(--on-scrim-muted)", ["--accent-ink" as string]: "var(--on-scrim)", ["--border" as string]: "rgb(255 255 255 / 0.28)" }
    : undefined;
  return (
    <Section slot="hero" tone={img ? "band" : tone} className="relative isolate overflow-hidden">
      {img && (
        <>
          <img src={asset(img.src)} alt={img.alt || ""} width={img.width} height={img.height} fetchPriority="high"
            className="absolute inset-0 -z-20 h-full w-full object-cover" />
          <div aria-hidden="true" className="absolute inset-0 -z-10"
            style={{ background: "linear-gradient(to top, var(--scrim-strong) 0%, var(--scrim-mid) 50%, var(--scrim-soft) 100%)" }} />
          {img.credit && <PhotoCredit text={img.credit} />}
        </>
      )}
      <div style={onPhoto}>
        {/* The grid, drawn: four hairline columns on the page container. */}
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
          {/* Phones keep only the outer frame, so no line runs through the text. */}
          <div className="wrap grid h-full grid-cols-1 md:grid-cols-4">
            {[0, 1, 2, 3].map((i) => (
              <div key={i} className={cn("border-l border-line", i === 0 ? "border-r md:border-r-0" : "hidden md:block", i === 3 && "border-r")} />
            ))}
          </div>
        </div>
        <div className="wrap flex min-h-[min(92svh,860px)] flex-col justify-end pb-10 pt-32 md:pb-14">
          <div className="hero-rise max-w-5xl">
            <T k="hero.headline" as="h1" className="t-display text-ink" />
          </div>
          {services.length > 0 && (
            <ul className="mt-10 grid grid-cols-2 border-t border-line md:grid-cols-4">
              {services.map((_, i) => (
                <li key={i} className="relative flex items-start gap-2 py-3 pr-4 md:py-4">
                  <GridMark className="mt-1.5 flex-none text-muted" />
                  <T k={`services.items.${i}.title`} className="text-step-small font-medium text-ink" />
                </li>
              ))}
            </ul>
          )}
          <div className="mt-8 grid gap-8 md:grid-cols-4 md:items-end">
            <div className="md:col-span-2">
              <T k="hero.subhead" as="p" className="t-lead max-w-xl" />
              <Actions slot="hero" whatsapp className="mt-6" />
              <HeroProof className="mt-5" />
            </div>
            <div className="rounded-theme-lg border-theme border-line p-5 backdrop-blur-sm md:col-span-1 md:col-start-4"
              style={{ background: img ? "var(--scrim-mid)" : "var(--surface)" }}>
              <PhoneBig className="min-h-11 justify-center [&>span:last-child]:text-step-3" />
              <T k="business.hours" as="p" className="mt-3 text-step-small text-muted" />
            </div>
          </div>
        </div>
      </div>
    </Section>
  );
}
