import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { content, ui } from "@/lib/content";

/** Heading beside spec-sheet rows: each reason a title and one line. */
export default function TrustGrid({ tone = "base" }: { tone?: Tone }) {
  const items = (content.trust?.items || []).filter((i) => i.title).slice(0, 6);
  if (!items.length) return null;
  return (
    <Section slot="trust" tone={tone} label={ui("whyChoose")}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:gap-16">
        <T k="trust.heading" as="h2" className="t-headline text-ink lg:col-span-4" fallback={ui("whyChoose")} />
        <dl className="border-b border-line lg:col-span-8">
          {items.map((_, i) => (
            <div key={i} className="grid gap-1.5 border-t border-line py-5 sm:grid-cols-[minmax(0,0.8fr)_minmax(0,1.2fr)] sm:gap-8">
              <T k={`trust.items.${i}.title`} as="dt" className="t-title text-ink" />
              <T k={`trust.items.${i}.text`} as="dd" className="text-muted sm:pt-1" />
            </div>
          ))}
        </dl>
      </div>
    </Section>
  );
}
