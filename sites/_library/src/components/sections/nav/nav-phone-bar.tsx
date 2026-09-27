import { BrandMark } from "@/components/BrandMark";
import { NavLinks } from "@/components/NavLinks";
import { NavMenu } from "@/components/NavMenu";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PhoneIcon } from "@/components/icons";
import { content, phone, primaryHref, telHref, ui } from "@/lib/content";

/** A band-tone utility strip (what we do + the number) above a sticky main bar. */
export default function NavPhoneBar({ tone = "base" }: { tone?: Tone }) {
  return (
    <>
      <div data-slot="nav" data-tone="band" className="relative z-30">
        <div className="wrap flex min-h-10 items-center justify-between gap-4 py-1.5 text-step-small">
          <T k="nav.note" as="p" className="hidden truncate text-muted sm:block" />
          {phone ? (
            <a href={telHref} className="ml-auto inline-flex items-center gap-2 font-semibold text-ink no-underline hover:text-accent-ink sm:ml-0">
              <PhoneIcon aria-hidden="true" className="h-4 w-4 text-accent-ink" strokeWidth={2} />
              <span className="num-tabular" data-edit="business.phone.display">{phone.display}</span>
            </a>
          ) : (
            <T k="business.hours" as="p" className="text-muted" />
          )}
        </div>
      </div>
      <Section slot="nav" as="header" tone={tone} className="sticky top-0 z-30 border-b border-line">
        <nav aria-label={ui("mainNav")} className="wrap flex min-h-[4.25rem] items-center justify-between gap-4 py-2">
          <a href="#top" className="min-w-0 text-ink no-underline">
            <BrandMark nameClassName="text-[1.1rem] leading-tight md:text-[1.35rem]" />
          </a>
          <div className="flex items-center gap-7">
            <NavLinks />
            <a href={primaryHref} className="btn btn-primary hidden min-h-11 px-4 md:inline-flex">
              <T k="nav.cta" fallback={telHref ? ui("call") : ui("quote")} />
            </a>
            <NavMenu links={content.nav?.links || []} openLabel={ui("menuOpen")} closeLabel={ui("menuClose")} />
          </div>
        </nav>
      </Section>
    </>
  );
}
