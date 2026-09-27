import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, Coverage, Stars } from "@/components/parts";
import { content, reviewItems, ui } from "@/lib/content";

/**
 * The proof leads: a real Google review quoted at scale beside the
 * headline. With no reviews it falls back to headline + coverage only.
 */
export default function HeroReviewLed({ tone = "base" }: { tone?: Tone }) {
  if (!content.hero) return null;
  // The strongest short review: highest rating, then the one that reads best at size.
  const pick = [...reviewItems]
    .map((r, i) => ({ r, i }))
    .sort((a, b) => (b.r.rating || 5) - (a.r.rating || 5) || Math.abs(a.r.text.length - 160) - Math.abs(b.r.text.length - 160))[0];
  const rating = content.reviews?.rating;
  const count = content.reviews?.count;
  return (
    <Section slot="hero" tone={tone}>
      <div className="wrap grid gap-12 py-12 md:py-20 lg:grid-cols-12 lg:gap-16">
        <div className="hero-rise lg:col-span-6">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-5 max-w-xl" />
          <Coverage className="mt-6 text-step-small" />
          <Actions slot="hero" whatsapp className="mt-8" />
        </div>
        {pick && (
          <figure className="relative self-center lg:col-span-6">
            {rating ? (
              <div className="mb-6 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <span className="t-phone text-step-4 text-ink">{rating.toFixed(1)}</span>
                <Stars value={rating} className="text-xl" />
                {count ? <span className="text-muted">{ui("fromReviews", { count })}</span> : null}
              </div>
            ) : null}
            <blockquote className="rule border-t-theme pt-6">
              <p data-edit={`reviews.items.${pick.i}.text`} className="font-display text-step-2 leading-snug text-ink"
                style={{ textTransform: "none", letterSpacing: "var(--display-tracking)" }}>
                “{pick.r.text}”
              </p>
            </blockquote>
            <figcaption className="mt-5 flex items-center gap-3 text-muted">
              <Stars value={pick.r.rating || 5} />
              <span className="t-label" data-edit={`reviews.items.${pick.i}.author`}>{pick.r.author}</span>
              <span aria-hidden="true">·</span>
              <span className="t-label">{ui("googleReview")}</span>
            </figcaption>
          </figure>
        )}
      </div>
    </Section>
  );
}
