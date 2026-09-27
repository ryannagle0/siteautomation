import { ContactForm } from "@/components/ContactForm";
import { ContactList } from "@/components/ContactList";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { formText } from "@/components/formText";
import { content } from "@/lib/content";

/**
 * A dark, final "let's talk" (labs): details on the left, and a short form
 * that opens with tap-to-choose service chips — less typing on a phone.
 */
export default function ContactChips({ tone = "band" }: { tone?: Tone }) {
  if (!content.contact?.heading) return null;
  return (
    <Section slot="contact" id="contact" tone={tone}>
      <div className="wrap section-y grid gap-12 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-5">
          <T k="contact.heading" as="h2" className="t-headline text-ink" />
          <T k="contact.intro" as="p" className="t-lead mt-4" />
          <ContactList className="mt-8 [&>div:last-child]:border-b" />
        </div>
        <div className="lg:col-span-7">
          <ContactForm t={formText(true)} chips />
        </div>
      </div>
    </Section>
  );
}
