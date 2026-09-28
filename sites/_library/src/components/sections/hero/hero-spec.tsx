import type { ReactNode } from "react";
import { PhotoCredit } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, Stars } from "@/components/parts";
import { asset, biz, content, hasImage, phone, towns, ui } from "@/lib/content";
import { cn } from "@/lib/cn";

/**
 * Spec Sheet template hero: a heavy headline with its last phrase run
 * through the brand colour like a highlighter, and the facts set out as a
 * spec table under their photo: where, when, how they're rated, the number.
 */
export default function HeroSpec({ tone = "base" }: { tone?: Tone }) {
  const hero = content.hero;
  if (!hero) return null;
  const img = hasImage(hero.image) ? hero.image : null;
  // Highlight what follows the last comma ("Commercial power, on programme.").
  const cut = hero.headline.lastIndexOf(",");
  const head = cut > 0 && cut < hero.headline.length - 3 ? [hero.headline.slice(0, cut + 1), hero.headline.slice(cut + 1)] : [hero.headline, ""];
  const r = content.reviews;
  const covering: ReactNode = towns.length ? (
    <>
      {towns.slice(0, 3).map((t, i) => (
        <span key={i}><span data-edit={`area.towns.${i}`}>{t}</span>{i < Math.min(towns.length, 3) - 1 ? ", " : ""}</span>
      ))}
      {towns.length > 3 && ` ${ui("more")}`}
    </>
  ) : biz.county ? <>Co. <span data-edit="business.county">{biz.county}</span></> : biz.town ? <span data-edit="business.town">{biz.town}</span> : null;
  const rows: { label: string; value: ReactNode; edit?: string }[] = [
    ...(covering ? [{ label: ui("specCovering"), value: covering }] : []),
    ...(biz.hours ? [{ label: ui("hours"), value: biz.hours, edit: "business.hours" }] : []),
    ...(r?.rating ? [{ label: ui("specRating"), value: (
      <span className="inline-flex flex-wrap items-center gap-2"><Stars value={r.rating} className="text-sm" />
        {r.count ? ui("ratingLine", { rating: r.rating.toFixed(1), count: r.count }) : r.rating.toFixed(1)}</span>) }] : []),
    ...(phone ? [{ label: ui("phone"), value: phone.display, edit: "business.phone.display" }] : []),
  ];
  return (
    <Section slot="hero" tone={tone}>
      <div className="wrap">
        <div className="grid border-b-theme border-line lg:grid-cols-12">
          <div className={cn("hero-rise py-12 md:py-16", img ? "lg:col-span-7 lg:border-r-theme lg:border-line lg:pr-12" : "lg:col-span-12")}>
            <h1 data-edit="hero.headline" className="t-display text-ink">
              {head[0]}
              {head[1] && <>{" "}<mark className="spec-mark">{head[1].trim()}</mark></>}
            </h1>
            <T k="hero.subhead" as="p" className="t-lead mt-7 max-w-xl" />
            <Actions slot="hero" className="mt-9" />
          </div>
          {/* No photo: the spec table runs as one row under the headline. */}
          <div className={cn("flex flex-col", img ? "lg:col-span-5" : "lg:col-span-12")}>
            {img && (
              <div className="relative -mx-[var(--gutter)] min-h-[15rem] flex-1 overflow-hidden bg-surface-2 lg:mx-0">
                <img src={asset(img.src)} alt={img.alt || ""} width={img.width} height={img.height} fetchPriority="high"
                  className="absolute inset-0 h-full w-full object-cover" />
                {img.credit && <PhotoCredit text={img.credit} />}
              </div>
            )}
            {rows.length > 0 && (
              <dl className={cn("grid grid-cols-[auto_1fr] max-lg:-mx-[var(--gutter)]", !img && "lg:grid-flow-col lg:grid-cols-none lg:auto-cols-auto")}>
                {rows.map((row, i) => (
                  <div key={i} className="contents">
                    <dt className="t-label flex items-center border-r-theme border-t-theme border-line px-[var(--gutter)] py-3.5 text-ink lg:px-5">{row.label}</dt>
                    <dd {...(row.edit ? { "data-edit": row.edit } : {})}
                      className="flex items-center border-t-theme border-line px-5 py-3.5 font-semibold text-ink"><span>{row.value}</span></dd>
                  </div>
                ))}
              </dl>
            )}
          </div>
        </div>
      </div>
    </Section>
  );
}
