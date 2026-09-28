import { GridMark } from "@/components/GridMark";
import { HeroProof } from "@/components/HeroProof";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, Coverage } from "@/components/parts";
import { content } from "@/lib/content";

/**
 * The business's own colour owns the first screen (labs). One hue only:
 * a soft tonal field from the accent into its own shade, "+" marks at the
 * grid corners, the headline mid-left and the services on a rule along the
 * bottom. Built for leads with no photos.
 */
export default function HeroColourField({ tone = "accent" }: { tone?: Tone }) {
  if (!content.hero) return null;
  const services = (content.services?.items || []).filter((s) => s.title).slice(0, 4);
  return (
    <Section slot="hero" tone={tone} className="relative isolate overflow-hidden">
      <div aria-hidden="true" className="absolute inset-0 -z-10"
        style={{
          background:
            // One hue, darkened only toward the empty top-right corner, so the
            // small text below always sits on the true accent (contrast-checked).
            "radial-gradient(90% 80% at 100% 0%, color-mix(in oklab, var(--accent) 78%, black) 0%, transparent 60%), var(--accent)",
        }} />
      <div className="wrap relative flex min-h-[min(86svh,780px)] flex-col pb-10 pt-16 md:pb-12 md:pt-24">
        <div aria-hidden="true" className="flex justify-between text-muted">
          <GridMark />
          <GridMark />
        </div>
        <div className="hero-rise my-auto max-w-4xl py-12">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-6 max-w-2xl" />
          <Coverage className="mt-5 text-step-small" />
        </div>
        <div className="grid gap-8 border-t border-line pt-6 lg:grid-cols-12 lg:items-end">
          {services.length > 0 && (
            <ul className="grid grid-cols-2 gap-x-6 gap-y-3 md:grid-cols-4 lg:col-span-7">
              {services.map((_, i) => (
                <li key={i}>
                  <T k={`services.items.${i}.title`} className="t-label text-ink" />
                </li>
              ))}
            </ul>
          )}
          <div className="lg:col-span-5 lg:justify-self-end">
            <Actions slot="hero" whatsapp className="lg:justify-end" />
            <HeroProof className="mt-4 lg:justify-end" />
          </div>
        </div>
      </div>
    </Section>
  );
}
