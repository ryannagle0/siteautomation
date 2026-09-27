import { HeroProof } from "@/components/HeroProof";
import { Img } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, Coverage, PhoneBig } from "@/components/parts";
import { content, hasImage } from "@/lib/content";

/**
 * Words, then a three-photo mosaic (one tall, two stacked). Two or fewer
 * photos collapse gracefully: one photo sits alone, none shows the phone panel.
 */
export default function HeroImageGrid({ tone = "base" }: { tone?: Tone }) {
  const hero = content.hero;
  if (!hero) return null;
  const imgs = [...(hero.images || []), ...(hasImage(hero.image) ? [hero.image] : [])].filter(hasImage).slice(0, 3);
  return (
    <Section slot="hero" tone={tone} className="overflow-hidden">
      <div className="wrap grid gap-10 py-12 md:py-20 lg:grid-cols-2 lg:items-center lg:gap-14">
        <div className="hero-rise">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-5 max-w-xl" />
          <Coverage className="mt-6 text-step-small" />
          <Actions slot="hero" whatsapp className="mt-8" />
          <HeroProof className="mt-7" />
        </div>
        {imgs.length >= 3 ? (
          <div className="grid aspect-[5/4] grid-cols-2 grid-rows-2 gap-3 md:gap-4">
            <Img img={imgs[0]} priority ratio={null} sizes="(min-width: 1024px) 25vw, 50vw" className="row-span-2 h-full" />
            <Img img={imgs[1]} ratio={null} sizes="(min-width: 1024px) 25vw, 50vw" className="h-full" />
            <Img img={imgs[2]} ratio={null} sizes="(min-width: 1024px) 25vw, 50vw" className="h-full" />
          </div>
        ) : imgs.length > 0 ? (
          <Img img={imgs[0]} priority ratio="4 / 3" sizes="(min-width: 1024px) 50vw, 100vw" />
        ) : (
          <div className="rule border-t-theme pt-8 lg:border-l-theme lg:border-t-0 lg:pl-12 lg:pt-0">
            <PhoneBig />
            <T k="business.hours" as="p" className="mt-4 text-muted" />
          </div>
        )}
      </div>
    </Section>
  );
}
