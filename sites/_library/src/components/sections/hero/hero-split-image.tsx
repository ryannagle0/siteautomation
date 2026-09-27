import { HeroProof } from "@/components/HeroProof";
import { Img } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Actions, Coverage, PhoneBig } from "@/components/parts";
import { content, hasImage } from "@/lib/content";

/**
 * Words left, one photo right. Without a photo, the right column becomes
 * the van-door panel: the phone number at display size, hours, coverage.
 */
export default function HeroSplitImage({ tone = "base" }: { tone?: Tone }) {
  const hero = content.hero;
  if (!hero) return null;
  const img = hasImage(hero.image) ? hero.image : null;
  return (
    <Section slot="hero" tone={tone} className="overflow-hidden">
      <div className="wrap grid items-center gap-10 py-12 md:grid-cols-12 md:gap-12 md:py-20 lg:py-24">
        <div className="hero-rise md:col-span-7">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-5 max-w-xl" />
          <Coverage className="mt-6 text-step-small" />
          <Actions slot="hero" whatsapp className="mt-8" />
          <HeroProof className="mt-7" />
        </div>
        <div className="md:col-span-5">
          {img ? (
            <Img img={img} priority ratio="4 / 3" sizes="(min-width: 768px) 40vw, 100vw" className="w-full md:!aspect-[4/5] md:max-h-[70vh]" />
          ) : (
            <div className="rule border-t-theme pt-8 md:border-l-theme md:border-t-0 md:pl-10 md:pt-0">
              <PhoneBig />
              <T k="business.hours" as="p" className="mt-5 text-muted" />
            </div>
          )}
        </div>
      </div>
    </Section>
  );
}
