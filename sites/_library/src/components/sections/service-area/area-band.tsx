import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { towns } from "@/lib/content";

/**
 * Van Livery template: the towns in a band of brand colour, set in the
 * signwriting face like the list on a van door. Home town first, marked
 * with the hi-vis stripe.
 */
export default function AreaBand({ tone = "band" }: { tone?: Tone }) {
  const list = towns.slice(0, 10);
  if (!list.length) return null;
  return (
    <Section slot="service-area" id="area" tone={tone}>
      <div className="wrap flex flex-col gap-4 py-8 md:flex-row md:items-baseline md:gap-10 md:py-9">
        <T k="area.heading" as="h2" className="t-label flex-none text-ink" />
        <ul className="flex flex-wrap gap-x-7 gap-y-2">
          {list.map((town, i) => (
            <li key={i} data-edit={`area.towns.${i}`}
              className={i === 0 ? "van-home font-display text-step-2 leading-none text-ink" : "font-display text-step-2 leading-none text-ink"}
              style={{ fontWeight: "var(--display-weight)", textTransform: "var(--display-case)" as never, letterSpacing: "0.02em" }}>
              {town}
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
