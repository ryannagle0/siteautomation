import { BrandMark } from "@/components/BrandMark";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { content, phone, telHref, ui } from "@/lib/content";

/** One quiet row: name, links, number, legal line. */
export default function FooterSimple({ tone = "base" }: { tone?: Tone }) {
  const links = content.nav?.links || [];
  return (
    <Section slot="footer" as="footer" tone={tone} className="border-t border-line">
      <div className="wrap flex flex-col gap-6 py-10 md:flex-row md:items-center md:justify-between">
        <div>
          <BrandMark nameClassName="text-lg leading-tight" />
          <T k="footer.blurb" as="p" className="mt-2 text-step-small text-muted" />
        </div>
        <nav aria-label={ui("footerNav")}>
          <ul className="flex flex-wrap gap-x-6 gap-y-2 text-step-small">
            {links.map((l, i) => (
              <li key={i}>
                <a href={l.href} className="text-muted no-underline hover:text-ink">{l.label}</a>
              </li>
            ))}
            {phone && (
              <li>
                <a href={telHref} className="font-semibold text-ink no-underline tabular-nums">{phone.display}</a>
              </li>
            )}
          </ul>
        </nav>
      </div>
      <div className="wrap border-t border-line py-5">
        <T k="footer.legal" as="p" className="text-step--2 text-muted" />
      </div>
    </Section>
  );
}
