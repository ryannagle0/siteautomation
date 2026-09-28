import { HeroProof } from "@/components/HeroProof";
import { PhotoCredit } from "@/components/Img";
import { QuickQuote } from "@/components/QuickQuote";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PhoneIcon } from "@/components/icons";
import { Coverage } from "@/components/parts";
import { asset, biz, content, hasImage, phone, telHref, ui } from "@/lib/content";
import { cn } from "@/lib/cn";

/**
 * Quote Box template hero. The first screen is the quote request itself:
 * a box to describe the job with the services as one-tap chips, sending
 * straight into the contact form (prefilled). Beside it, their photo and
 * the number, for people who'd rather ring.
 */
export default function HeroQuoteBox({ tone = "base" }: { tone?: Tone }) {
  const hero = content.hero;
  if (!hero) return null;
  const img = hasImage(hero.image) ? hero.image : null;
  const services = (content.contact?.services || content.services?.items?.map((s) => s.title) || []).filter(Boolean);
  const owner = biz.ownerFirstName;
  return (
    <Section slot="hero" tone={tone}>
      <div className="wrap grid gap-12 pb-16 pt-12 md:pb-24 md:pt-20 lg:grid-cols-12 lg:items-end lg:gap-14">
        <div className="hero-rise lg:col-span-7">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-6 max-w-2xl" />
          <QuickQuote className="mt-9 rounded-theme-lg border-[1.5px] border-ink bg-surface p-4 shadow-[0_24px_48px_-28px_rgb(0_0_0/0.45)] md:p-5"
            label={owner ? ui("quoteBoxLabel", { name: owner }) : ui("quickQuoteLabel")}
            placeholder={ui("quoteBoxPlaceholder") || ui("quickQuotePlaceholder")}
            submit={ui("quoteBoxSubmit") || ui("quickQuoteSubmit")} services={services} />
          <HeroProof className="mt-6" />
        </div>
        <aside aria-label={ui("contactNav")} className="lg:col-span-5">
          {img && (
            <div className="media relative mb-7 aspect-[4/3] lg:aspect-[4/4.2]">
              <img src={asset(img.src)} alt={img.alt || ""} width={img.width} height={img.height} fetchPriority="high" />
              {img.credit && <PhotoCredit text={img.credit} />}
            </div>
          )}
          {phone && (
            <a href={telHref} className={cn("group block no-underline", !img && "rounded-theme-lg border border-line bg-surface p-7")}>
              <span className="t-label block text-muted">{ui("orJustRing")}</span>
              <span className="mt-2 flex items-center gap-3">
                <PhoneIcon aria-hidden="true" className="h-8 w-8 flex-none text-accent-ink" strokeWidth={2} />
                <span data-edit="business.phone.display" className="t-phone text-step-4 text-ink transition-colors group-hover:text-accent-ink">
                  {phone.display}
                </span>
              </span>
            </a>
          )}
          <T k="business.hours" as="p" className="mt-4 text-step-small text-muted" />
          <Coverage className="mt-2 text-step-small" max={4} />
        </aside>
      </div>
    </Section>
  );
}
