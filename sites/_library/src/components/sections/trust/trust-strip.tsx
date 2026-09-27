import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { content, ui } from "@/lib/content";

/** Three or four short promises in a ruled row under the hero; type only, no icon tiles. */
export default function TrustStrip({ tone = "surface" }: { tone?: Tone }) {
  const items = (content.trust?.items || []).filter((i) => i.title).slice(0, 4);
  if (!items.length) return null;
  return (
    <Section slot="trust" tone={tone} label={ui("whyChoose")}>
      <ul className="wrap grid py-6 sm:grid-cols-2 md:py-8 lg:grid-flow-col lg:grid-cols-none lg:auto-cols-fr">
        {items.map((item, i) => (
          <li key={i} className="border-t border-line py-5 first:border-t-0 sm:[&:nth-child(2)]:border-t-0 lg:border-l lg:border-t-0 lg:px-8 lg:py-2 lg:first:border-l-0 lg:first:pl-0">
            <T k={`trust.items.${i}.title`} as="p" className="text-step-1 font-semibold leading-snug text-ink" />
            <T k={`trust.items.${i}.text`} as="p" className="mt-1 text-step-small leading-snug text-muted" />
          </li>
        ))}
      </ul>
    </Section>
  );
}
