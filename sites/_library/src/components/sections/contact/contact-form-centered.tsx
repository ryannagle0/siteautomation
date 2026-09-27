import { ContactForm } from "@/components/ContactForm";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { formText } from "@/components/formText";
import { PhoneIcon, WhatsAppIcon } from "@/components/icons";
import { content, phone, telHref, ui, waHref } from "@/lib/content";

/**
 * A single focused column on the page's left edge: heading, form, and the
 * call/WhatsApp alternatives beside it on desktop (under it on phones).
 * (The id is kept for existing sites; the column is no longer centred so it
 * lines up with the nav and every other section.)
 */
export default function ContactFormCentered({ tone = "surface" }: { tone?: Tone }) {
  if (!content.contact?.heading) return null;
  return (
    <Section slot="contact" id="contact" tone={tone}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-7">
          <T k="contact.heading" as="h2" className="t-headline text-ink" />
          <T k="contact.intro" as="p" className="t-lead mt-4 max-w-lg" />
          <ContactForm t={formText()} className="mt-10 rounded-theme-lg bg-bg p-6 md:p-10" />
        </div>
        {phone && (
          <div className="flex flex-col gap-3 lg:col-span-4 lg:col-start-9 lg:pt-24">
            <a href={telHref} className="inline-flex min-h-11 items-center gap-3 border-t border-line pt-4 font-semibold text-ink no-underline hover:text-accent-ink">
              <PhoneIcon aria-hidden="true" className="h-5 w-5 text-accent-ink" strokeWidth={2} />
              <span data-edit="business.phone.display" className="tabular-nums">{phone.display}</span>
            </a>
            {waHref && (
              <a href={waHref} target="_blank" rel="noopener" className="inline-flex min-h-11 items-center gap-3 border-t border-line pt-4 font-semibold text-ink no-underline hover:text-accent-ink">
                <WhatsAppIcon aria-hidden="true" className="h-5 w-5 text-accent-ink" strokeWidth={2} />
                {ui("whatsapp")}
              </a>
            )}
          </div>
        )}
      </div>
    </Section>
  );
}
