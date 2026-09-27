import { BrandMark } from "@/components/BrandMark";
import { ContactList } from "@/components/ContactList";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { content, towns, ui } from "@/lib/content";

/** Band-tone footer: who, how to reach, where, and the page links. */
export default function FooterColumns({ tone = "band" }: { tone?: Tone }) {
  const links = content.nav?.links || [];
  return (
    <Section slot="footer" as="footer" tone={tone}>
      <div className="wrap grid gap-10 py-14 md:grid-cols-2 lg:grid-cols-12 lg:gap-12 lg:py-20">
        <div className="lg:col-span-4">
          <BrandMark nameClassName="text-xl leading-tight" />
          <T k="footer.blurb" as="p" className="mt-4 max-w-xs text-muted" />
        </div>
        <div className="lg:col-span-4">
          <ContactList area={towns.length === 0} className="[&>div:first-child]:border-t-0 [&>div:first-child]:pt-0" />
        </div>
        {towns.length > 0 && (
          <div className="lg:col-span-2">
            <p className="t-label text-muted">{ui("area")}</p>
            <ul className="mt-4 space-y-2 text-step-small">
              {towns.slice(0, 8).map((t, i) => (
                <li key={i} className="text-ink">{t}</li>
              ))}
            </ul>
          </div>
        )}
        {links.length > 0 && (
          <nav aria-label={ui("footerNav")} className="lg:col-span-2">
            <ul className="space-y-2 text-step-small">
              {links.map((l, i) => (
                <li key={i}>
                  <a href={l.href} className="text-ink no-underline hover:text-accent-ink">{l.label}</a>
                </li>
              ))}
            </ul>
          </nav>
        )}
      </div>
      <div className="wrap border-t border-line py-6">
        <T k="footer.legal" as="p" className="text-step--2 text-muted" />
      </div>
    </Section>
  );
}
