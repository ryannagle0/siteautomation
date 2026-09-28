import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Heading } from "@/components/parts";
import { content } from "@/lib/content";

/** Quote Box template: how it works, as three or four plain numbered steps. */
export default function ProcessCircles({ tone = "base" }: { tone?: Tone }) {
  const steps = (content.process?.steps || []).filter((s) => s.title).slice(0, 4);
  if (!steps.length) return null;
  return (
    <Section slot="process" id="process" tone={tone} className="border-t border-line">
      <div className="wrap section-y">
        <Heading k="process.heading" intro="process.intro" />
        <ol className="mt-12 grid gap-10 md:grid-flow-col md:auto-cols-fr md:gap-8">
          {steps.map((_, i) => (
            <li key={i} className="max-w-sm">
              <span aria-hidden="true"
                className="grid h-12 w-12 place-items-center rounded-full bg-ink text-step-1 font-bold text-bg">{i + 1}</span>
              <T k={`process.steps.${i}.title`} as="h3" className="t-title mt-5 text-ink" />
              <T k={`process.steps.${i}.text`} as="p" className="mt-2 text-muted" />
            </li>
          ))}
        </ol>
      </div>
    </Section>
  );
}
