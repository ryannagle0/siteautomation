import { Review, ReviewsHeader, ReviewsLink } from "@/components/ReviewParts";
import { Section, type Tone } from "@/components/Section";
import { hasReviews, reviewItems } from "@/lib/content";

/** One review quoted large, the next few beside it. Renders only with real reviews. */
export default function ReviewsFeatured({ tone = "surface" }: { tone?: Tone }) {
  if (!hasReviews) return null;
  const rest = reviewItems.slice(1, 4);
  return (
    <Section slot="reviews" id="reviews" tone={tone}>
      <div className="wrap section-y">
        <ReviewsHeader />
        <div className="mt-12 grid gap-12 lg:grid-cols-12 lg:gap-16">
          <Review i={0} size="lg" className={rest.length ? "self-start lg:col-span-7" : "self-start lg:col-span-10"} />
          {rest.length > 0 && (
            <div className="grid gap-8 lg:col-span-5">
              {rest.map((_, j) => (
                <Review key={j} i={j + 1} className="rule border-t-theme pt-6" />
              ))}
            </div>
          )}
        </div>
        <ReviewsLink className="mt-10" />
      </div>
    </Section>
  );
}
