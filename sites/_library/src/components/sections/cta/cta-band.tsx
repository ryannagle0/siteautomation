import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, PhoneBig } from "@/components/parts";
import { content } from "@/lib/content";

/** Full-width band: the ask on the left, the number huge on the right. */
export default function CtaBand({ tone = "band" }: { tone?: Tone }) {
  if (!content.cta?.heading) return null;
  return (
    <Section slot="cta" tone={tone}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:items-end lg:gap-16">
        <div className="lg:col-span-7">
          <T k="cta.heading" as="h2" className="t-headline text-ink" />
          <T k="cta.text" as="p" className="t-lead mt-4 max-w-xl" />
          <Actions slot="cta" whatsapp className="mt-8" />
        </div>
        <div className="lg:col-span-5 lg:text-right">
          <PhoneBig className="lg:items-end" />
        </div>
      </div>
    </Section>
  );
}
