import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PinIcon } from "@/components/icons";
import { content, towns } from "@/lib/content";

/**
 * The signature section: the towns set as large type, like the list on a
 * van door or a road sign. Home town marked with the pin.
 */
export default function AreaTowns({ tone = "base" }: { tone?: Tone }) {
  const list = towns.slice(0, 16);
  if (!content.area?.heading || !list.length) return null;
  const home = (content.business.town || "").toLowerCase();
  return (
    <Section slot="service-area" id="area" tone={tone}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-4">
          <T k="area.heading" as="h2" className="t-headline text-ink" />
          <T k="area.intro" as="p" className="t-lead mt-4" />
          <T k="area.note" as="p" className="mt-6 text-muted" />
        </div>
        <ul className="flex flex-wrap content-start items-baseline gap-x-6 gap-y-2 lg:col-span-8">
          {list.map((town, i) => {
            const isHome = town.toLowerCase().startsWith(home) && !!home;
            return (
              <li key={i} className="flex items-baseline gap-2">
                {isHome && <PinIcon aria-hidden="true" className="h-[0.8em] w-[0.8em] self-center text-accent-ink" strokeWidth={2.2} />}
                <span data-edit={`area.towns.${i}`}
                  className={`font-display text-step-3 leading-tight ${isHome ? "text-accent-ink" : "text-ink"}`}
                  style={{ fontWeight: "var(--display-weight)", letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)" as never }}>
                  {town}
                </span>
                {i < list.length - 1 && <span aria-hidden="true" className="text-step-2 text-muted opacity-60">/</span>}
              </li>
            );
          })}
        </ul>
      </div>
    </Section>
  );
}
