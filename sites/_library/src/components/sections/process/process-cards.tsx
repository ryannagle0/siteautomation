import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Heading } from "@/components/parts";
import { content } from "@/lib/content";

/** Steps as tinted panels with a large numeral; compact, good after a long services list. */
export default function ProcessCards({ tone = "base" }: { tone?: Tone }) {
  const steps = (content.process?.steps || []).filter((s) => s.title).slice(0, 4);
  if (!steps.length) return null;
  return (
    <Section slot="process" id="process" tone={tone}>
      <div className="wrap section-y">
        <Heading k="process.heading" intro="process.intro" align="center" />
        <ol className={`mx-auto mt-12 grid max-w-5xl gap-4 sm:grid-cols-2 ${steps.length === 3 ? "lg:grid-cols-3" : "lg:grid-cols-4"}`}>
          {steps.map((_, i) => (
            <li key={i} className="rounded-theme-lg bg-accent-soft p-6 md:p-7">
              <span aria-hidden="true" className="t-phone block text-step-3 text-accent-ink">{i + 1}</span>
              <T k={`process.steps.${i}.title`} as="h3" className="t-title mt-5 text-ink" />
              <T k={`process.steps.${i}.text`} as="p" className="mt-2 text-muted" />
            </li>
          ))}
        </ol>
      </div>
    </Section>
  );
}
