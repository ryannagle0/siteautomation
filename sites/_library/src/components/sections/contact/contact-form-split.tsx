import { ContactForm } from "@/components/ContactForm";
import { ContactList } from "@/components/ContactList";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { formText } from "@/components/formText";
import { content } from "@/lib/content";

/** Details and reassurance on the left, the quote form on the right. */
export default function ContactFormSplit({ tone = "base" }: { tone?: Tone }) {
  if (!content.contact?.heading) return null;
  return (
    <Section slot="contact" id="contact" tone={tone}>
      <div className="wrap section-y grid gap-12 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-5">
          <T k="contact.heading" as="h2" className="t-headline text-ink" />
          <T k="contact.intro" as="p" className="t-lead mt-4" />
          <ContactList className="mt-8 [&>div:last-child]:border-b" />
        </div>
        <div className="rounded-theme-lg bg-surface p-6 md:p-10 lg:col-span-7">
          <ContactForm t={formText(true)} />
        </div>
      </div>
    </Section>
  );
}
