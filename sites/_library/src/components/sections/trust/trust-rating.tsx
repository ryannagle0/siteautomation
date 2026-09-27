import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Icon, ExternalIcon } from "@/components/icons";
import { Stars } from "@/components/parts";
import { content, ui } from "@/lib/content";

/**
 * The Google rating as the headline trust signal, with the promises beside
 * it. Without a rating it's the same row of promises on its own.
 */
export default function TrustRating({ tone = "surface" }: { tone?: Tone }) {
  const items = (content.trust?.items || []).filter((i) => i.title).slice(0, 3);
  const rating = content.reviews?.rating;
  const count = content.reviews?.count;
  if (!items.length && !rating) return null;
  return (
    <Section slot="trust" tone={tone} label={ui("whyChoose")}>
      <div className="wrap grid gap-8 py-10 md:py-12 lg:grid-cols-12 lg:items-center lg:gap-12">
        {rating ? (
          <div className="lg:col-span-4">
            <div className="flex items-baseline gap-3">
              <span className="t-phone text-step-5 text-ink">{rating.toFixed(1)}</span>
              <Stars value={rating} className="text-2xl" />
            </div>
            <p className="mt-3 text-muted">
              {count ? ui("reviewsOn", { count }) : ui("ratedOn")}
              {content.reviews?.link ? (
                <>
                  {" · "}
                  <a href={content.reviews.link} target="_blank" rel="noopener" className="link inline-flex items-center gap-1">
                    {ui("readReviews")} <ExternalIcon aria-hidden="true" className="h-4 w-4" />
                  </a>
                </>
              ) : null}
            </p>
          </div>
        ) : null}
        {items.length > 0 && (
          <ul className={`grid gap-6 sm:grid-cols-3 ${rating ? "lg:col-span-8" : "lg:col-span-12"}`}>
            {items.map((item, i) => (
              <li key={i} className="rule border-t-theme pt-4">
                <div className="flex items-center gap-2.5">
                  <Icon name={item.icon} className="h-5 w-5 flex-none text-accent-ink" />
                  <T k={`trust.items.${i}.title`} as="p" className="font-semibold text-ink" />
                </div>
                <T k={`trust.items.${i}.text`} as="p" className="mt-1.5 text-step-small text-muted" />
              </li>
            ))}
          </ul>
        )}
      </div>
    </Section>
  );
}
