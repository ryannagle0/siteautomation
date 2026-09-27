import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { content } from "@/lib/content";

/** Story on the left, a ruled list of plain facts (base, hours, coverage) on the right. */
export default function AboutFacts({ tone = "base" }: { tone?: Tone }) {
  const about = content.about;
  if (!about?.heading) return null;
  const body = (about.body || []).filter(Boolean);
  const facts = (about.facts || []).filter((f) => f.label && f.value);
  return (
    <Section slot="about" id="about" tone={tone}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className={facts.length ? "lg:col-span-7" : "lg:col-span-9"}>
          <T k="about.heading" as="h2" className="t-headline text-ink" />
          <div className="t-body mt-6 text-muted">
            {body.map((_, i) => (
              <T key={i} k={`about.body.${i}`} as="p" className={i === 0 ? "text-step-1 text-ink" : ""} />
            ))}
          </div>
        </div>
        {facts.length > 0 && (
          <dl className="self-end lg:col-span-5">
            {facts.map((_, i) => (
              <div key={i} className="grid grid-cols-[minmax(7rem,auto)_1fr] gap-4 border-t border-line py-4 last:border-b">
                <T k={`about.facts.${i}.label`} as="dt" className="t-label pt-0.5 text-muted" />
                <T k={`about.facts.${i}.value`} as="dd" className="font-semibold text-ink" />
              </div>
            ))}
          </dl>
        )}
      </div>
    </Section>
  );
}
