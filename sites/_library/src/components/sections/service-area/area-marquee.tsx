import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PinIcon } from "@/components/icons";
import { content, towns, ui } from "@/lib/content";

/**
 * The towns as a slow band of display type (labs) — the one thing on the
 * page that can loop honestly. Pauses on hover; with reduced motion it's a
 * still, wrapped list. The second copy of the list is decorative only.
 */
export default function AreaMarquee({ tone = "accent" }: { tone?: Tone }) {
  const list = towns.slice(0, 12);
  if (!content.area?.heading || list.length < 3) return null;
  const row = (hidden: boolean) => (
    <ul aria-hidden={hidden || undefined} className="marquee-row flex shrink-0 items-center gap-8 pr-8">
      {list.map((town, i) => (
        <li key={i} className="flex items-center gap-8">
          <span {...(!hidden ? { "data-edit": `area.towns.${i}` } : {})}
            className="whitespace-nowrap font-display text-step-4 leading-none text-ink"
            style={{ fontWeight: "var(--display-weight)", letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)" as never }}>
            {town}
          </span>
          <PinIcon aria-hidden="true" className="h-6 w-6 flex-none text-muted" strokeWidth={1.6} />
        </li>
      ))}
    </ul>
  );
  return (
    <Section slot="service-area" id="area" tone={tone} className="overflow-hidden">
      <div className="wrap pt-12 md:pt-16">
        <T k="area.heading" as="h2" className="t-headline text-ink" />
        <T k="area.intro" as="p" className="t-lead mt-3 max-w-2xl" />
      </div>
      <div className="marquee mt-10 border-y border-line py-8 md:py-10" role="region" aria-label={ui("areaMarquee")}>
        <div className="marquee-track flex w-max">
          {row(false)}
          {row(true)}
        </div>
      </div>
      {content.area.note ? (
        <div className="wrap pb-12 pt-6 md:pb-16">
          <T k="area.note" as="p" className="text-muted" />
        </div>
      ) : (
        <div className="pb-12 md:pb-16" />
      )}
    </Section>
  );
}
