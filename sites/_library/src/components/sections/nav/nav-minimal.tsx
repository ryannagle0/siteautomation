import { BrandMark } from "@/components/BrandMark";
import { NavLinks } from "@/components/NavLinks";
import { NavMenu } from "@/components/NavMenu";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PhoneIcon } from "@/components/icons";
import { content, primaryHref, telHref, ui } from "@/lib/content";

/** Brand left, links and one call button right. Sticky, quiet. */
export default function NavMinimal({ tone = "base" }: { tone?: Tone }) {
  return (
    <Section slot="nav" as="header" tone={tone} className="sticky top-0 z-30 border-b border-line">
      <nav aria-label={ui("mainNav")} className="wrap flex min-h-[4.25rem] items-center justify-between gap-4 py-2">
        <a href="#top" className="min-w-0 text-ink no-underline">
          <BrandMark nameClassName="text-[1.05rem] leading-tight md:text-[1.2rem]" />
        </a>
        <div className="flex items-center gap-7">
          <NavLinks />
          <a href={primaryHref} className="btn btn-primary hidden min-h-11 px-4 md:inline-flex">
            {telHref && <PhoneIcon aria-hidden="true" strokeWidth={2} />}
            <T k="nav.cta" fallback={telHref ? ui("call") : ui("quote")} />
          </a>
          <NavMenu links={content.nav?.links || []} openLabel={ui("menuOpen")} closeLabel={ui("menuClose")} />
        </div>
      </nav>
    </Section>
  );
}
