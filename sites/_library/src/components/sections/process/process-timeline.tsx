import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { content } from "@/lib/content";

/** Heading left, a vertical line of steps right with numbered markers. */
export default function ProcessTimeline({ tone = "surface" }: { tone?: Tone }) {
  const steps = (content.process?.steps || []).filter((s) => s.title).slice(0, 6);
  if (!steps.length) return null;
  return (
    <Section slot="process" id="process" tone={tone}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-5">
          <T k="process.heading" as="h2" className="t-headline text-ink" />
          <T k="process.intro" as="p" className="t-lead mt-4" />
        </div>
        <ol className="relative lg:col-span-7">
          <span aria-hidden="true" className="absolute bottom-6 left-5 top-6 w-px bg-line" />
          {steps.map((_, i) => (
            <li key={i} className="relative grid grid-cols-[2.5rem_1fr] gap-x-6 pb-10 last:pb-0">
              <span aria-hidden="true"
                className="relative z-10 flex h-10 w-10 items-center justify-center rounded-full border-theme border-accent bg-bg font-semibold tabular-nums text-accent-ink">
                {i + 1}
              </span>
              <div className="pt-1.5">
                <T k={`process.steps.${i}.title`} as="h3" className="t-title text-ink" />
                <T k={`process.steps.${i}.text`} as="p" className="mt-2 text-muted" />
              </div>
            </li>
          ))}
        </ol>
      </div>
    </Section>
  );
}
