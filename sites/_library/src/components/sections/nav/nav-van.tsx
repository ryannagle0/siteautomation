import { BrandMark } from "@/components/BrandMark";
import { NavLinks } from "@/components/NavLinks";
import { NavMenu } from "@/components/NavMenu";
import { Section, type Tone } from "@/components/Section";
import { PhoneIcon } from "@/components/icons";
import { content, phone, telHref, ui } from "@/lib/content";

/** Van Livery template: the name signwritten in the brand colour, like the van. */
export default function NavVan({ tone = "base" }: { tone?: Tone }) {
  return (
    <Section slot="nav" as="header" tone={tone} className="sticky top-0 z-30 border-b border-line">
      <nav aria-label={ui("mainNav")} className="wrap flex min-h-[4.75rem] items-center justify-between gap-4 py-2">
        <a href="#top" className="min-w-0 text-accent-ink no-underline">
          <BrandMark nameClassName="text-[1.5rem] leading-none md:text-[1.9rem]" />
        </a>
        <div className="flex items-center gap-7">
          <NavLinks />
          {phone && (
            <a href={telHref} aria-label={ui("callNumber", { phone: phone.display })}
              className="hidden min-h-11 items-center gap-2 font-bold text-ink no-underline hover:text-accent-ink md:inline-flex">
              <PhoneIcon aria-hidden="true" className="h-[1.1em] w-[1.1em] text-accent-ink" strokeWidth={2.2} />
              <span data-edit="business.phone.display" className="t-phone text-step-2">{phone.display}</span>
            </a>
          )}
          <NavMenu links={content.nav?.links || []} openLabel={ui("menuOpen")} closeLabel={ui("menuClose")} />
        </div>
      </nav>
    </Section>
  );
}
