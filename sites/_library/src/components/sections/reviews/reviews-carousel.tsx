import { Review, ReviewsHeader, ReviewsLink } from "@/components/ReviewParts";
import { Section, type Tone } from "@/components/Section";
import { hasReviews, reviewItems, ui } from "@/lib/content";

/** A horizontal, swipeable row of reviews (native scroll-snap, no script). Renders only with real reviews. */
export default function ReviewsCarousel({ tone = "surface" }: { tone?: Tone }) {
  if (!hasReviews) return null;
  const items = reviewItems.slice(0, 8);
  return (
    <Section slot="reviews" id="reviews" tone={tone} className="overflow-hidden">
      <div className="wrap section-y">
        <ReviewsHeader />
        <div
          role="region"
          aria-label={ui("googleReview")}
          tabIndex={0}
          className="-mx-gutter mt-12 flex snap-x snap-mandatory gap-5 overflow-x-auto scroll-px-gutter px-gutter pb-4 [scrollbar-width:thin]"
        >
          {items.map((_, i) => (
            <Review key={i} i={i}
              className="w-[85%] flex-none snap-start rounded-theme-lg border-theme border-line bg-bg p-6 sm:w-[26rem] md:p-8" />
          ))}
        </div>
        <ReviewsLink className="mt-8" />
      </div>
    </Section>
  );
}
