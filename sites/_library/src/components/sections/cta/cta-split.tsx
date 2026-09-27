import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { ContactList } from "@/components/ContactList";
import { Actions } from "@/components/parts";
import { content } from "@/lib/content";

/** Ask on one side, every contact route on the other. */
export default function CtaSplit({ tone = "surface" }: { tone?: Tone }) {
  if (!content.cta?.heading) return null;
  return (
    <Section slot="cta" tone={tone}>
      <div className="wrap section-y grid gap-10 md:grid-cols-2 md:gap-16">
        <div>
          <T k="cta.heading" as="h2" className="t-headline text-ink" />
          <T k="cta.text" as="p" className="t-lead mt-4 max-w-md" />
          <Actions slot="cta" whatsapp className="mt-8" />
        </div>
        <ContactList className="self-center [&>div:last-child]:border-b" />
      </div>
    </Section>
  );
}
