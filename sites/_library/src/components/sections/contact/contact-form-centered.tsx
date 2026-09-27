import { ContactForm } from "@/components/ContactForm";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { formText } from "@/components/formText";
import { PhoneIcon, WhatsAppIcon } from "@/components/icons";
import { content, phone, telHref, ui, waHref } from "@/lib/content";

/** A single centred column: heading, form, and the call/WhatsApp alternatives under it. */
export default function ContactFormCentered({ tone = "surface" }: { tone?: Tone }) {
  if (!content.contact?.heading) return null;
  return (
    <Section slot="contact" id="contact" tone={tone}>
      <div className="wrap section-y">
        <div className="mx-auto max-w-2xl">
          <div className="text-center">
            <T k="contact.heading" as="h2" className="t-headline text-ink" />
            <T k="contact.intro" as="p" className="t-lead mx-auto mt-4 max-w-lg" />
          </div>
          <ContactForm t={formText()} className="mt-10 rounded-theme-lg bg-bg p-6 md:p-10" />
          {phone && (
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row sm:gap-8">
              <a href={telHref} className="inline-flex min-h-11 items-center gap-2 font-semibold text-ink no-underline hover:text-accent-ink">
                <PhoneIcon aria-hidden="true" className="h-5 w-5 text-accent-ink" strokeWidth={2} />
                <span data-edit="business.phone.display" className="tabular-nums">{phone.display}</span>
              </a>
              {waHref && (
                <a href={waHref} target="_blank" rel="noopener" className="inline-flex min-h-11 items-center gap-2 font-semibold text-ink no-underline hover:text-accent-ink">
                  <WhatsAppIcon aria-hidden="true" className="h-5 w-5 text-accent-ink" strokeWidth={2} />
                  {ui("whatsapp")}
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </Section>
  );
}
