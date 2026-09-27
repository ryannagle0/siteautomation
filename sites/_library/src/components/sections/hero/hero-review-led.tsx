import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, Coverage, Stars } from "@/components/parts";
import { content, heroQuote, ui } from "@/lib/content";

/**
 * The proof leads: one real Google review, quoted at scale beside the
 * headline (the quote card IS the hero's rating moment — no separate badge).
 * With no reviews it falls back to headline + coverage only.
 */
export default function HeroReviewLed({ tone = "base" }: { tone?: Tone }) {
  if (!content.hero) return null;
  const quote = heroQuote();
  return (
    <Section slot="hero" tone={tone}>
      <div className="wrap grid gap-12 py-12 md:py-20 lg:grid-cols-12 lg:gap-16">
        <div className="hero-rise lg:col-span-6">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-5 max-w-xl" />
          <Coverage className="mt-6 text-step-small" />
          <Actions slot="hero" whatsapp className="mt-8" />
        </div>
        {quote && (
          <figure className="self-center rounded-theme-lg bg-surface p-6 md:p-10 lg:col-span-6">
            <Stars value={quote.rating} className="text-xl" />
            <blockquote className="mt-5">
              <p data-edit={quote.path ? `${quote.path}.text` : undefined} className="text-step-2 font-medium leading-snug text-ink">
                “{quote.text}”
              </p>
            </blockquote>
            <figcaption className="mt-6 flex flex-wrap items-center gap-x-2 text-step-small text-muted">
              <span className="font-semibold text-ink" data-edit={quote.path ? `${quote.path}.author` : undefined}>{quote.author}</span>
              <span aria-hidden="true">·</span>
              <span>{ui("googleReview")}</span>
            </figcaption>
          </figure>
        )}
      </div>
    </Section>
  );
}
