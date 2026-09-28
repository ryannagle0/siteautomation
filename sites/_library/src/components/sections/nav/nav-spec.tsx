import { BrandMark } from "@/components/BrandMark";
import { NavLinks } from "@/components/NavLinks";
import { NavMenu } from "@/components/NavMenu";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PhoneIcon } from "@/components/icons";
import { content, phone, primaryHref, telHref, ui } from "@/lib/content";

/**
 * Spec Sheet template: a black strip with what they do and the number,
 * then the name, links and a solid call button on a 2px rule.
 */
export default function NavSpec({ tone = "base" }: { tone?: Tone }) {
  return (
    <Section slot="nav" as="header" tone={tone} className="sticky top-0 z-30">
      <div data-tone="band" className="text-step--1">
        <div className="wrap flex min-h-10 items-center justify-between gap-4">
          <T k="nav.note" as="p" className="hidden truncate text-muted sm:block" />
          {phone && (
            <a href={telHref} className="ml-auto inline-flex min-h-10 items-center gap-2 font-semibold text-ink no-underline">
              <PhoneIcon aria-hidden="true" className="h-3.5 w-3.5" strokeWidth={2.2} />
              <span data-edit="business.phone.display">{phone.display}</span>
            </a>
          )}
        </div>
      </div>
      <nav aria-label={ui("mainNav")} className="wrap">
        <div className="flex min-h-[4.5rem] items-center justify-between gap-4 border-b-theme border-line">
          <a href="#top" className="min-w-0 text-ink no-underline">
            <BrandMark nameClassName="text-[1.2rem] leading-none md:text-[1.45rem]" />
          </a>
          <div className="flex items-center gap-7">
            <NavLinks />
            <span className="hidden md:block">
              <a href={primaryHref} className="btn min-h-11 border-theme border-ink bg-ink px-5 text-bg hover:bg-transparent hover:text-ink">
                <T k="nav.cta" fallback={telHref ? ui("call") : ui("quote")} />
              </a>
            </span>
            <NavMenu links={content.nav?.links || []} openLabel={ui("menuOpen")} closeLabel={ui("menuClose")} />
          </div>
        </div>
      </nav>
    </Section>
  );
}
