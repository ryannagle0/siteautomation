import { T } from "@/components/T";
import { ExternalIcon } from "@/components/icons";
import { Stars } from "@/components/parts";
import { content, reviewItems, ui } from "@/lib/content";
import { cn } from "@/lib/cn";

/** Heading row for review sections: title, overall rating, link to Google. */
export function ReviewsHeader({ className, align = "left" }: { className?: string; align?: "left" | "center" }) {
  const r = content.reviews;
  return (
    <div className={cn("flex flex-col gap-6 md:flex-row md:items-end md:justify-between", align === "center" && "items-center text-center md:flex-col md:items-center", className)}>
      <div className="max-w-2xl">
        <T k="reviews.heading" as="h2" className="t-headline text-ink" />
        <T k="reviews.intro" as="p" className="t-lead mt-4" />
      </div>
      {r?.rating ? (
        <div className={cn("flex flex-col gap-1.5", align === "left" && "md:items-end md:text-right")}>
          <div className="flex items-center gap-3">
            <span className="t-phone text-step-3 text-ink">{r.rating.toFixed(1)}</span>
            <Stars value={r.rating} className="text-xl" />
          </div>
          {r.count ? <span className="text-step-small text-muted">{ui("reviewsOn", { count: r.count })}</span> : null}
        </div>
      ) : null}
    </div>
  );
}

export function ReviewsLink({ className }: { className?: string }) {
  const r = content.reviews;
  if (!r?.link) return null;
  return (
    <a href={r.link} target="_blank" rel="noopener" className={cn("link inline-flex items-center gap-1.5", className)}>
      <T k="reviews.linkLabel" fallback={ui("readReviews")} />
      <ExternalIcon aria-hidden="true" className="h-4 w-4" />
    </a>
  );
}

/** One review: stars, text, author · when · source. `i` indexes content.reviews.items. */
export function Review({ i, size = "md", className }: { i: number; size?: "md" | "lg"; className?: string }) {
  const r = reviewItems[i];
  if (!r) return null;
  const index = (content.reviews?.items || []).indexOf(r);
  return (
    <figure className={cn("flex flex-col", className)}>
      <Stars value={r.rating || 5} className={size === "lg" ? "text-xl" : "text-base"} />
      <blockquote className="mt-4">
        <p data-edit={`reviews.items.${index}.text`}
          className={size === "lg" ? "font-display text-step-3 leading-[1.2] text-ink" : "leading-relaxed text-ink"}
          style={size === "lg" ? { textTransform: "none", letterSpacing: "var(--display-tracking)" } : undefined}>
          “{r.text}”
        </p>
      </blockquote>
      <figcaption className={cn("pt-5 text-step-small text-muted", size === "md" && "mt-auto")}>
        <span data-edit={`reviews.items.${index}.author`} className="font-semibold text-ink">{r.author}</span>
        {r.when ? <span data-edit={`reviews.items.${index}.when`}> · {r.when}</span> : null}
        <span> · {ui("googleReview")}</span>
      </figcaption>
    </figure>
  );
}
