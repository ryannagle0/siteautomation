import { FitWord } from "@/components/FitWord";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { biz, content, mailHref, phone, telHref, ui } from "@/lib/content";

/**
 * The business name at poster scale, cropped by the bottom edge (labs).
 * It is measured to span the container exactly, whatever the name's
 * length or the preset's font; the contact line sits above it.
 */
export default function FooterWordmark({ tone = "band" }: { tone?: Tone }) {
  const name = biz.name || "";
  const links = content.nav?.links || [];
  return (
    <Section slot="footer" as="footer" tone={tone} className="overflow-hidden">
      <div className="wrap pt-14 md:pt-20">
        <div className="grid gap-6 border-b border-line pb-8 md:grid-cols-12 md:items-end">
          {(phone || biz.email) && <div className="md:col-span-5">
            {phone && (
              <p>
                <a href={telHref} className="t-phone inline-flex min-h-11 items-center text-step-3 text-ink no-underline hover:text-accent-ink">
                  <span data-edit="business.phone.display">{phone.display}</span>
                </a>
              </p>
            )}
            {biz.email && (
              <a href={mailHref} data-edit="business.email" className="mt-3 block break-words text-muted no-underline hover:text-ink">{biz.email}</a>
            )}
          </div>}
          <nav aria-label={ui("footerNav")} className={phone || biz.email ? "md:col-span-4" : "md:col-span-9"}>
            <ul className="flex flex-wrap gap-x-6 gap-y-2 text-step-small">
              {links.map((l, i) => (
                <li key={i}><a href={l.href} className="text-ink no-underline hover:text-accent-ink">{l.label}</a></li>
              ))}
            </ul>
          </nav>
          <div className="text-step--2 text-muted md:col-span-3 md:text-right">
            <T k="footer.legal" as="p" />
            <a href="#top" className="mt-1 inline-block text-muted no-underline hover:text-ink">{ui("backToTop")}</a>
          </div>
        </div>
        {/* Sized to the container by measurement; the crop is visual only
            (the full name stays in the text). */}
        <div className="mt-8">
          <FitWord text={name} data-edit="business.name" className="font-display text-ink"
            style={{ height: "0.8em", overflow: "hidden", lineHeight: 0.95, fontWeight: "var(--display-weight)" as never,
              letterSpacing: "var(--display-tracking)", textTransform: "var(--display-case)" as never }} />
        </div>
      </div>
    </Section>
  );
}
