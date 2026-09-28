import { HeroProof } from "@/components/HeroProof";
import { PhotoCredit } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions } from "@/components/parts";
import { asset, content, hasImage, phone, telHref, ui } from "@/lib/content";
import { cn } from "@/lib/cn";

/**
 * Van Livery template hero: the phone number is the headline, set like
 * the signwriting on the side of the van, with the livery's sweep of brand
 * colour and a hi-vis stripe behind their photo. The sentence under it is
 * the h1 (what they do, where).
 */
export default function HeroVan({ tone = "base" }: { tone?: Tone }) {
  const hero = content.hero;
  if (!hero) return null;
  const img = hasImage(hero.image) ? hero.image : null;
  return (
    <Section slot="hero" tone={tone} className="hero-van relative isolate overflow-hidden border-b-[10px] border-accent">
      {/* The livery: a raked block of brand colour with a hi-vis pinstripe. */}
      <div aria-hidden="true" className="van-sweep pointer-events-none absolute inset-y-0 right-0 -z-10 hidden w-[46%] md:block" />
      <div aria-hidden="true" className="h-2 bg-[var(--livery)] md:hidden" />
      <div className={cn("wrap grid gap-10 pb-14 pt-10 md:pb-20 md:pt-16 lg:items-center", img && "lg:grid-cols-12 lg:gap-12")}>
        <div className={cn("hero-rise", img ? "lg:col-span-7" : "md:max-w-[58%]")}>
          {phone ? (
            <a href={telHref} aria-label={ui("callNumber", { phone: phone.display })}
              className="block text-ink no-underline hover:text-accent-ink">
              <span data-edit="business.phone.display" className="van-number t-phone block">{phone.display}</span>
            </a>
          ) : null}
          <T k="hero.headline" as="h1" className="mt-5 max-w-xl font-body text-step-2 font-semibold normal-case leading-snug tracking-normal text-ink" />
          <T k="hero.subhead" as="p" className="mt-3 max-w-xl text-muted" />
          <Actions slot="hero" whatsapp className="mt-8" />
          <HeroProof className="mt-6" />
        </div>
        {img && (
          <div className="lg:col-span-5">
            <div className="media relative aspect-[16/11]">
              <img src={asset(img.src)} alt={img.alt || ""} width={img.width} height={img.height} fetchPriority="high" />
              {img.credit && <PhotoCredit text={img.credit} />}
            </div>
          </div>
        )}
      </div>
    </Section>
  );
}
