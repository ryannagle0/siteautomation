import { FuseBoard } from "@/components/FuseBoard";
import { HeroProof } from "@/components/HeroProof";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { WireStripe } from "@/components/WireStripe";
import { Icon } from "@/components/icons";
import { Actions, Coverage, PhoneBig } from "@/components/parts";
import { content } from "@/lib/content";

/**
 * Electrician hero (labs mockup). No photo needed: a consumer unit drawn
 * large, fed by brown, blue and green-and-yellow cable cores dropping in
 * from above, its breakers switching on as the page loads. The main
 * services sit under the headline with the electrician icon set, and the
 * three cores close the section as a stripe. Readable as "electrician"
 * before a word of the copy is read.
 */
export default function HeroElectric({ tone = "base" }: { tone?: Tone }) {
  if (!content.hero) return null;
  const services = (content.services?.items || []).filter((s) => s.title).slice(0, 4);
  return (
    <Section slot="hero" tone={tone} className="relative isolate overflow-hidden">
      {/* Phones: board first (the cables drop straight into it), then the
          words, then the number. Desktop: words left, board and number right. */}
      <div className="wrap grid gap-10 pb-16 pt-8 md:pb-20 md:pt-16 lg:grid-cols-12 lg:gap-x-10 lg:gap-y-8 lg:pt-20">
        <div className="lg:col-span-5 lg:col-start-8 lg:row-start-1 lg:self-end">
          <FuseBoard className="block w-full max-w-[340px] text-ink sm:max-w-[420px] lg:max-w-none" />
        </div>
        <div className="hero-rise lg:col-span-7 lg:col-start-1 lg:row-span-2 lg:row-start-1 lg:self-center">
          <T k="hero.headline" as="h1" className="t-display text-ink" />
          <T k="hero.subhead" as="p" className="t-lead mt-6 max-w-2xl" />
          <Actions slot="hero" whatsapp className="mt-9" />
          <HeroProof className="mt-6" />
          {services.length > 0 && (
            <ul className="mt-10 grid grid-cols-2 gap-x-6 gap-y-5 border-t border-line pt-6 sm:grid-cols-4">
              {services.map((s, i) => (
                <li key={i} className="flex flex-col gap-2.5">
                  <Icon name={s.icon} className="h-8 w-8 text-accent-ink" strokeWidth={1.5} />
                  <T k={`services.items.${i}.title`} className="text-step-small font-semibold leading-snug text-ink" />
                </li>
              ))}
            </ul>
          )}
        </div>
        <div className="flex flex-wrap items-end justify-between gap-x-8 gap-y-3 border-t border-line pt-6 lg:col-span-5 lg:col-start-8 lg:row-start-2 lg:self-start">
          <PhoneBig />
          <div className="text-step-small">
            <T k="business.hours" as="p" className="text-muted" />
            <Coverage className="mt-1" max={3} />
          </div>
        </div>
      </div>
      <WireStripe className="absolute inset-x-0 bottom-0" />
    </Section>
  );
}
