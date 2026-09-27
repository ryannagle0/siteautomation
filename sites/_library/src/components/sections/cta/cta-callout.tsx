import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions } from "@/components/parts";
import { content } from "@/lib/content";

/** A contained accent panel inside the page's flow; lighter than a full band. */
export default function CtaCallout({ tone = "base" }: { tone?: Tone }) {
  if (!content.cta?.heading) return null;
  return (
    <Section slot="cta" tone={tone}>
      <div className="wrap py-[calc(var(--section-y)*0.6)]">
        <div data-tone="accent" className="flex flex-col gap-8 rounded-theme-lg px-6 py-10 md:flex-row md:items-center md:justify-between md:px-12 md:py-12">
          <div className="max-w-xl">
            <T k="cta.heading" as="h2" className="t-headline text-ink" />
            <T k="cta.text" as="p" className="mt-3 text-step-1 text-muted" />
          </div>
          <Actions slot="cta" whatsapp className="flex-none md:flex-col lg:flex-row" />
        </div>
      </div>
    </Section>
  );
}
