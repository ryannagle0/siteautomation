import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Heading } from "@/components/parts";
import { content } from "@/lib/content";

/**
 * A two-column ruled list, like a price board without the prices: each
 * service a title and one line. No icon tiles; the words carry it.
 */
export default function ServicesGrid({ tone = "base" }: { tone?: Tone }) {
  const items = (content.services?.items || []).filter((s) => s.title);
  if (!items.length) return null;
  return (
    <Section slot="services" id="services" tone={tone}>
      <div className="wrap section-y">
        <Heading k="services.heading" intro="services.intro" />
        <ul className="mt-12 grid gap-x-14 md:grid-cols-2">
          {items.map((_, i) => (
            <li key={i} className="grid gap-2 border-t border-line py-6 md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)] md:gap-6">
              <T k={`services.items.${i}.title`} as="h3" className="t-title text-ink" />
              <T k={`services.items.${i}.text`} as="p" className="text-muted md:pt-1" />
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
