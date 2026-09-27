import { HeroProof } from "@/components/HeroProof";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Icon } from "@/components/icons";
import { Actions, Coverage, PhoneBig } from "@/components/parts";
import { content } from "@/lib/content";

/**
 * No image by design: the headline at full display scale, and the contact
 * panel (number, hours, towns) set like the side of the van. Behind it, the
 * trade's own mark drawn as an oversized hairline outline in the brand
 * colour, so an image-less first screen isn't an empty wash.
 */
export default function HeroTypographic({ tone = "base" }: { tone?: Tone }) {
  if (!content.hero) return null;
  const mark = content.hero.icon;
  return (
    <Section slot="hero" tone={tone} className="isolate overflow-hidden">
      {mark && (
        <div aria-hidden="true" className="pointer-events-none absolute inset-0 -z-10">
          <div className="wrap relative h-full">
            <Icon name={mark} strokeWidth={0.6}
              className="hero-mark absolute -right-[18%] top-[42%] h-[min(34rem,95vw)] w-[min(34rem,95vw)] text-accent sm:-right-[6%] sm:top-[6%] lg:right-[-2%]" />
          </div>
        </div>
      )}
      <div className="wrap grid gap-12 py-14 md:py-24 lg:grid-cols-12 lg:items-end lg:gap-16">
        <div className="hero-rise lg:col-span-8">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-6 max-w-2xl" />
          <Actions slot="hero" whatsapp className="mt-9" />
        </div>
        <aside aria-label="Contact" className="rule border-t-theme pt-8 lg:col-span-4 lg:pb-2">
          <PhoneBig />
          <T k="business.hours" as="p" className="mt-4 text-muted" />
          <Coverage className="mt-5 text-step-small" />
          <HeroProof className="mt-5" />
        </aside>
      </div>
    </Section>
  );
}
