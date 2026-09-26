import Image from "next/image";
import { FadeUp } from "./motion/FadeUp";
import { CheckIcon, PhoneIcon } from "./icons";

const BULLETS = [
  "Safe Electric registered — certified on every job",
  "Fully insured for domestic and commercial",
  "Based in {{TOWN}}, on the road across {{TOWN}} daily",
  "Written quote before we start — no hidden costs",
];

const STATS = [
  { value: "20+", label: "Years" },
  { value: "{{TOWN}}", label: "Coverage Area" },
  { value: "100%", label: "Certified" },
  { value: "Free", label: "Quotes" },
];

export function About() {
  return (
    <section data-slot="about" id="about" className="bg-navy px-6 py-24 lg:px-16 lg:py-36">
      <div className="mx-auto grid max-w-content gap-14 lg:grid-cols-2 lg:gap-20">
        <FadeUp>
          <div className="relative h-[340px] overflow-hidden rounded-sharp lg:h-full lg:min-h-[520px]">
            <Image
              src="https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=800&auto=format&fit=crop"
              alt="{{OWNER_FIRST_NAME}} on site"
              fill
              sizes="(min-width: 1024px) 40vw, 100vw"
              className="object-cover"
            />
            <div className="absolute inset-0 bg-navy/35" />
          </div>
        </FadeUp>

        <FadeUp delay={0.1}>
          <p className="text-[13px] font-semibold uppercase tracking-wide text-blue">
            Who We Are
          </p>
          <h2 className="mt-4 text-balance text-4xl font-semibold tracking-tightest text-white sm:text-[2.75rem]">
            A local team. Not a call centre.
          </h2>
          <p className="mt-6 max-w-lg text-[15.5px] leading-relaxed text-white/55">
            {{BUSINESS_NAME}} has been serving {{TOWN}}
            for over 20 years. When you call, you speak to {{OWNER_FIRST_NAME}} — the
            person who will actually be on your job. Family owned, fully
            certified, and available 24/7 for emergencies.
          </p>

          <ul className="mt-8 flex flex-col gap-3.5">
            {BULLETS.map((b) => (
              <li key={b} className="flex items-start gap-3">
                <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-sharp bg-blue/15 text-blue">
                  <CheckIcon width={13} height={13} strokeWidth={2.4} />
                </span>
                <span className="text-[14.5px] text-white/75">{b}</span>
              </li>
            ))}
          </ul>

          <div className="mt-10 grid grid-cols-2 gap-x-6 gap-y-7 border-t border-white/10 pt-8">
            {STATS.map((s) => (
              <div key={s.label}>
                <p className="num-tabular text-2xl font-semibold tracking-tightest text-blue">
                  {s.value}
                </p>
                <p className="mt-1 text-[12px] font-medium uppercase tracking-wide text-white/40">
                  {s.label}
                </p>
              </div>
            ))}
          </div>

          <a
            href="tel:{{PHONE_TEL}}"
            className="mt-10 inline-flex items-center gap-2.5 rounded-sharp bg-blue px-7 py-4 text-[15px] font-semibold text-accent-foreground transition-colors hover:bg-blue-dark"
          >
            <PhoneIcon width={18} height={18} />
            Call {{OWNER_FIRST_NAME}} — {{PHONE_DISPLAY}}
          </a>
        </FadeUp>
      </div>
    </section>
  );
}
