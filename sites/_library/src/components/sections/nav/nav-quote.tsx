import { BrandMark } from "@/components/BrandMark";
import { Section, type Tone } from "@/components/Section";
import { PhoneIcon } from "@/components/icons";
import { phone, telHref, ui } from "@/lib/content";

/**
 * Quote Box template: the name and the number, nothing else. The page's
 * one job is a quote or a call, so the header doesn't compete with it.
 */
export default function NavQuote({ tone = "base" }: { tone?: Tone }) {
  return (
    <Section slot="nav" as="header" tone={tone} className="sticky top-0 z-30 border-b border-line">
      <nav aria-label={ui("mainNav")} className="wrap flex min-h-[4.5rem] items-center justify-between gap-4 py-2">
        <a href="#top" className="min-w-0 text-ink no-underline">
          <BrandMark nameClassName="text-[1.1rem] leading-tight md:text-[1.25rem]" />
        </a>
        {phone && (
          <a href={telHref} aria-label={ui("callNumber", { phone: phone.display })}
            className="inline-flex min-h-11 flex-none items-center gap-2 font-bold text-ink no-underline hover:text-accent-ink">
            <PhoneIcon aria-hidden="true" className="h-[1.1em] w-[1.1em] text-accent-ink" strokeWidth={2.2} />
            <span data-edit="business.phone.display" className="t-phone hidden text-step-1 sm:inline">{phone.display}</span>
          </a>
        )}
      </nav>
    </Section>
  );
}
