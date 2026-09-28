import { Review, ReviewsHeader, ReviewsLink } from "@/components/ReviewParts";
import { Section, type Tone } from "@/components/Section";
import { reviewItems } from "@/lib/content";
import { cn } from "@/lib/cn";

/**
 * Template reviews: the rating up top, then three real reviews as cards.
 * Each template dresses the card through its preset (see globals.css
 * .review-card): soft cards, a livery top edge, or ruled boxes.
 */
export default function ReviewsCards({ tone = "base" }: { tone?: Tone }) {
  const items = reviewItems.slice(0, 3);
  if (!items.length) return null;
  return (
    <Section slot="reviews" id="reviews" tone={tone}>
      <div className="wrap section-y">
        <ReviewsHeader />
        <div className={cn("mt-12 grid gap-4 md:gap-5", items.length > 1 && "md:grid-cols-2", items.length > 2 && "lg:grid-cols-3")}>
          {items.map((_, i) => (
            <Review key={i} i={i} className="review-card border-theme border-line bg-bg p-6 md:p-7" />
          ))}
        </div>
        <ReviewsLink className="mt-10" />
      </div>
    </Section>
  );
}
