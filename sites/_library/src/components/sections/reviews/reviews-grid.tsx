import { Review, ReviewsHeader, ReviewsLink } from "@/components/ReviewParts";
import { Section, type Tone } from "@/components/Section";
import { hasReviews, reviewItems } from "@/lib/content";

/** Every review in balanced columns, each under a rule. Renders only with real reviews. */
export default function ReviewsGrid({ tone = "base" }: { tone?: Tone }) {
  if (!hasReviews) return null;
  const items = reviewItems.slice(0, 6);
  const cols = items.length >= 3 ? "md:columns-2 lg:columns-3" : items.length === 2 ? "md:columns-2" : "";
  return (
    <Section slot="reviews" id="reviews" tone={tone}>
      <div className="wrap section-y">
        <ReviewsHeader />
        <div className={`mt-12 gap-10 ${cols}`}>
          {items.map((_, i) => (
            <Review key={i} i={i} className="rule mb-10 break-inside-avoid border-t-theme pt-6" />
          ))}
        </div>
        <ReviewsLink />
      </div>
    </Section>
  );
}
