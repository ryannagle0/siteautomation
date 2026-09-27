import { T } from "@/components/T";
import { Stars } from "@/components/parts";
import { content, ui } from "@/lib/content";
import { cn } from "@/lib/cn";
import sections from "@/sections.json";

/** Rating line for heroes: stars + hero.note ("Rated 4.9 from 63 Google reviews"). Real data only. */
export function HeroProof({ className }: { className?: string }) {
  const rating = content.reviews?.rating;
  if (!content.hero?.note && !rating) return null;
  // trust-rating shows the rating large right below; say it once.
  if ((sections as { variant: string }[]).some((s) => s.variant === "trust-rating")) return null;
  return (
    <div className={cn("flex flex-wrap items-center gap-x-3 gap-y-1 text-step-small text-muted", className)}>
      {rating ? <Stars value={rating} className="text-[1.05rem]" /> : null}
      {content.hero?.note ? (
        <T k="hero.note" as="span" />
      ) : rating ? (
        <span>{content.reviews?.count ? ui("ratingLine", { rating: rating.toFixed(1), count: content.reviews.count }) : ui("ratedOn")}</span>
      ) : null}
    </div>
  );
}
