import { BrandMark } from "@/components/BrandMark";
import { NavMenu } from "@/components/NavMenu";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PhoneIcon } from "@/components/icons";
import { content, phone, telHref, ui } from "@/lib/content";

/**
 * Shopfront-fascia header: the name centred like a painted board, a double
 * rule beneath, links set in a row under it. Phone on the right on desktop.
 */
export default function NavCentredLogo({ tone = "base" }: { tone?: Tone }) {
  const links = content.nav?.links || [];
  return (
    <Section slot="nav" as="header" tone={tone} className="relative z-30">
      <div className="wrap">
        {/* The name is centred on the header's own centre line (not a grid
            column), so a long note or name can never push it off-centre. */}
        <div className="relative flex items-center justify-between gap-4 py-4 md:min-h-[5.75rem] md:py-6">
          <T k="nav.note" as="p" className="t-label hidden max-w-[26%] truncate text-muted lg:block" />
          <a href="#top"
            className="min-w-0 text-ink no-underline md:absolute md:left-1/2 md:top-1/2 md:max-w-[46%] md:-translate-x-1/2 md:-translate-y-1/2 md:text-center">
            <BrandMark nameClassName="text-[1.05rem] leading-tight sm:text-[1.2rem] md:text-[1.6rem]" />
          </a>
          <div className="ml-auto flex items-center justify-end gap-3">
            {phone && (
              <a href={telHref} className="hidden items-center gap-2 font-semibold text-ink no-underline hover:text-accent-ink md:inline-flex">
                <PhoneIcon aria-hidden="true" className="h-4 w-4 text-accent-ink" strokeWidth={2} />
                <span className="num-tabular" data-edit="business.phone.display">{phone.display}</span>
              </a>
            )}
            <NavMenu links={links} openLabel={ui("menuOpen")} closeLabel={ui("menuClose")} />
          </div>
        </div>
        {links.length > 0 && (
          <nav aria-label={ui("mainNav")} className="hidden border-y-[3px] border-double border-line md:block">
            <ul className="flex items-center justify-center gap-10 py-3">
              {links.map((l, i) => (
                <li key={i}>
                  <a href={l.href} data-edit={`nav.links.${i}.label`}
                    className="text-step-small font-medium text-ink no-underline underline-offset-4 hover:underline">
                    {l.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        )}
        <div className="border-b-[3px] border-double border-line md:hidden" />
      </div>
    </Section>
  );
}
