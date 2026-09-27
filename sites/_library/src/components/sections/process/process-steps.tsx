import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Heading } from "@/components/parts";
import { content } from "@/lib/content";

/** Numbered steps across a single rule: the sequence is the information. */
export default function ProcessSteps({ tone = "base" }: { tone?: Tone }) {
  const steps = (content.process?.steps || []).filter((s) => s.title).slice(0, 5);
  if (!steps.length) return null;
  return (
    <Section slot="process" id="process" tone={tone}>
      <div className="wrap section-y">
        <Heading k="process.heading" intro="process.intro" />
        <ol className="mt-12 grid gap-10 md:grid-flow-col md:auto-cols-fr md:gap-8">
          {steps.map((_, i) => (
            <li key={i} className="rule relative border-t-theme pt-6">
              <span aria-hidden="true" className="t-phone block text-step-4 text-accent-ink">{i + 1}</span>
              <T k={`process.steps.${i}.title`} as="h3" className="t-title mt-4 text-ink" />
              <T k={`process.steps.${i}.text`} as="p" className="mt-2 text-muted" />
            </li>
          ))}
        </ol>
      </div>
    </Section>
  );
}
