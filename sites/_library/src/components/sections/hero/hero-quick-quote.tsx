import { HeroProof } from "@/components/HeroProof";
import { QuickQuote } from "@/components/QuickQuote";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PhoneIcon } from "@/components/icons";
import { Coverage } from "@/components/parts";
import { content, phone, telHref, ui } from "@/lib/content";

/**
 * The hero is the start of the quote (labs): headline, then one box to
 * describe the job with the services as chips, sending straight into the
 * page's quote form. The phone sits right beside it for people who'd
 * rather ring. Needs a contact variant with a form (SiteForge ensures it).
 */
export default function HeroQuickQuote({ tone = "base" }: { tone?: Tone }) {
  if (!content.hero) return null;
  const services = (content.contact?.services || content.services?.items?.map((s) => s.title) || []).filter(Boolean);
  return (
    <Section slot="hero" tone={tone}>
      <div className="wrap grid gap-10 py-12 md:py-20 lg:grid-cols-12 lg:gap-16">
        <div className="hero-rise lg:col-span-7">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-5 max-w-xl" />
          <QuickQuote className="mt-8" label={ui("quickQuoteLabel")} placeholder={ui("quickQuotePlaceholder")}
            submit={ui("quickQuoteSubmit")} services={services} />
        </div>
        <aside aria-label={ui("contactNav")} className="rule self-end border-t-theme pt-8 lg:col-span-5 lg:col-start-8">
          {phone && (
            <a href={telHref} className="group flex flex-col no-underline">
              <span className="t-label text-muted">{ui("orCall")}</span>
              <span className="mt-2 flex items-center gap-3">
                <PhoneIcon aria-hidden="true" className="h-7 w-7 flex-none text-accent-ink" strokeWidth={1.8} />
                <span data-edit="business.phone.display" className="t-phone text-step-4 text-ink transition-colors group-hover:text-accent-ink">{phone.display}</span>
              </span>
            </a>
          )}
          <T k="business.hours" as="p" className="mt-4 text-muted" />
          <Coverage className="mt-5 text-step-small" />
          <HeroProof className="mt-5" />
        </aside>
      </div>
    </Section>
  );
}
