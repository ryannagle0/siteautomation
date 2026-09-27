import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { ExternalIcon, MailIcon, WhatsAppIcon } from "@/components/icons";
import { PhoneBig } from "@/components/parts";
import { biz, content, mailHref, ui, waHref } from "@/lib/content";

/** No form: the number at full size, then WhatsApp, email, hours and a Maps link. */
export default function ContactDetails({ tone = "surface" }: { tone?: Tone }) {
  if (!content.contact?.heading) return null;
  return (
    <Section slot="contact" id="contact" tone={tone}>
      <div className="wrap section-y">
        <T k="contact.heading" as="h2" className="t-headline text-ink" />
        <T k="contact.intro" as="p" className="t-lead mt-4 max-w-2xl" />
        <div className="mt-10 grid gap-10 border-t border-line pt-10 md:grid-cols-12">
          <div className="md:col-span-7">
            <PhoneBig className="[&>span:last-child]:text-step-5" />
            <T k="business.hours" as="p" className="mt-4 text-muted" />
          </div>
          <div className="flex flex-col items-start gap-4 md:col-span-5">
            {waHref && (
              <a href={waHref} target="_blank" rel="noopener" className="btn btn-primary btn-lg">
                <WhatsAppIcon aria-hidden="true" strokeWidth={2} /> {ui("whatsapp")}
              </a>
            )}
            {biz.email && (
              <a href={mailHref} className="btn btn-secondary btn-lg max-w-full">
                <MailIcon aria-hidden="true" strokeWidth={2} />
                <span data-edit="business.email" className="truncate">{biz.email}</span>
              </a>
            )}
            {biz.mapsUrl && (
              <a href={biz.mapsUrl} target="_blank" rel="noopener" className="link inline-flex items-center gap-1.5">
                {ui("openInMaps")} <ExternalIcon aria-hidden="true" className="h-4 w-4" />
              </a>
            )}
          </div>
        </div>
      </div>
    </Section>
  );
}
