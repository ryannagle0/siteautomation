import { getGoogleReviews } from "@/lib/googleReviews";
import { FadeUp, StaggerGrid, StaggerItem } from "./motion/FadeUp";
import { StarIcon, ArrowRightIcon } from "./icons";

function GoogleLogo() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden>
      <path
        fill="#4285F4"
        d="M23.5 12.3c0-.85-.08-1.66-.22-2.45H12v4.63h6.46c-.28 1.5-1.13 2.77-2.4 3.62v3h3.87c2.27-2.09 3.57-5.17 3.57-8.8Z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.96-1.07 7.94-2.9l-3.87-3c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.96H1.27v3.1C3.24 21.3 7.28 24 12 24Z"
      />
      <path
        fill="#FBBC05"
        d="M5.27 14.29a7.2 7.2 0 0 1 0-4.58v-3.1H1.27a12 12 0 0 0 0 10.78l4-3.1Z"
      />
      <path
        fill="#EA4335"
        d="M12 4.76c1.77 0 3.35.6 4.6 1.8l3.44-3.44C17.95 1.19 15.23 0 12 0 7.28 0 3.24 2.7 1.27 6.61l4 3.1C6.22 6.87 8.87 4.76 12 4.76Z"
      />
    </svg>
  );
}

export async function Reviews() {
  const { reviews, mapsUrl } = await getGoogleReviews();

  return (
    <section id="reviews" className="bg-grey-section px-6 py-24 lg:px-16 lg:py-36">
      <div className="mx-auto max-w-content">
        <FadeUp className="max-w-xl">
          <p className="text-[13px] font-semibold uppercase tracking-wide text-blue">
            Reviews
          </p>
          <h2 className="mt-4 text-balance text-4xl font-semibold tracking-tightest text-navy sm:text-[2.75rem]">
            What {{TOWN}} say.
          </h2>
        </FadeUp>

        <StaggerGrid className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {reviews.map((r) => (
            <StaggerItem key={r.author}>
              <div className="flex h-full flex-col rounded-sharp border border-grey-line bg-base p-7">
                <div className="flex items-center justify-between">
                  <div className="flex gap-0.5 text-blue">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <StarIcon
                        key={i}
                        className={i < r.rating ? "" : "opacity-20"}
                      />
                    ))}
                  </div>
                  <GoogleLogo />
                </div>
                <p className="mt-5 flex-1 text-[14.5px] leading-relaxed text-navy/70">
                  &ldquo;{r.text}&rdquo;
                </p>
                <div className="mt-6 flex items-center justify-between border-t border-grey-line pt-4">
                  <p className="text-sm font-semibold text-navy">{r.author}</p>
                  <p className="text-xs text-navy/40">{r.relativeTime}</p>
                </div>
              </div>
            </StaggerItem>
          ))}
        </StaggerGrid>

        <FadeUp delay={0.15} className="mt-12 flex justify-center">
          <a
            href={mapsUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-sharp bg-blue px-7 py-4 text-[15px] font-semibold text-white transition-colors hover:bg-blue-dark"
          >
            Leave us a Google Review
            <ArrowRightIcon width={17} height={17} />
          </a>
        </FadeUp>
      </div>
    </section>
  );
}
