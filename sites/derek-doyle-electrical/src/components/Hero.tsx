"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { ShieldCheckIcon, PhoneIcon, WhatsAppIcon } from "./icons";

const STATS = [
  { value: "20+", label: "Years Experience" },
  { value: "{{TOWN}}", label: "Coverage Area" },
  { value: "24/7", label: "Emergency Callout" },
  { value: "Free", label: "Written Quotes" },
];

export function Hero() {
  return (
    <section
      id="top"
      className="relative flex min-h-screen flex-col overflow-hidden bg-base pt-20"
    >
      <div className="relative flex flex-1 flex-col lg:flex-row">
        {/* Left: content */}
        <motion.div
          initial={{ opacity: 0, x: -24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="relative z-10 flex flex-1 flex-col justify-center px-6 py-14 lg:px-16 lg:py-0"
        >
          <p className="text-[13px] font-semibold uppercase tracking-wide text-blue">
            {{TOWN}} · Safe Electric Registered
          </p>
          <h1 className="mt-5 max-w-xl text-balance text-[2.6rem] font-semibold leading-[1.06] tracking-tightest text-navy sm:text-6xl">
            {{HERO_HEADLINE}}
          </h1>
          <p className="mt-6 max-w-md text-[17px] leading-relaxed text-navy/65">
            Domestic rewires, commercial fit-outs, EV chargers and emergency
            callouts — fully insured and on the road across {{TOWN}}.
          </p>

          <div className="mt-9 flex flex-col gap-3.5 sm:flex-row">
            <a
              href="tel:{{PHONE_TEL}}"
              className="flex items-center justify-center gap-2.5 rounded-sharp bg-blue px-7 py-4 text-[15px] font-semibold text-white transition-colors hover:bg-blue-dark"
            >
              <PhoneIcon width={18} height={18} />
              Call {{PHONE_DISPLAY}}
            </a>
            <a
              href="https://wa.me/{{PHONE_WA}}"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-center gap-2.5 rounded-sharp border border-navy/20 px-7 py-4 text-[15px] font-semibold text-navy transition-colors hover:border-navy hover:bg-navy hover:text-white"
            >
              <WhatsAppIcon width={18} height={18} />
              WhatsApp Us →
            </a>
          </div>
        </motion.div>

        {/* Right: photo with diagonal navy slash */}
        <motion.div
          initial={{ opacity: 0, x: 24 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
          className="relative h-[46vh] w-full lg:h-auto lg:w-[46%]"
        >
          {/* navy slash */}
          <div
            aria-hidden
            className="absolute inset-y-0 left-0 z-10 hidden w-24 bg-navy lg:block"
            style={{
              clipPath: "polygon(48% 0, 100% 0, 52% 100%, 0 100%)",
              left: "-3px",
            }}
          />
          <div
            className="relative h-full w-full"
            style={{
              clipPath:
                "polygon(7% 0%, 100% 0%, 100% 100%, 0% 100%)",
            }}
          >
            <Image
              src="/hero.jpg"
              alt="Electrician at work on a domestic installation"
              fill
              priority={true}
              quality={100}
              sizes="(min-width: 1024px) 46vw, 100vw"
              className="object-cover"
              style={{ objectPosition: "30% center" }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-navy/30 via-transparent to-transparent" />
          </div>

          {/* Floating badge */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="absolute bottom-6 right-6 z-20 flex items-center gap-3 rounded-sharp bg-white px-4 py-3.5 shadow-[0_8px_24px_-8px_rgba(10,22,40,0.35)]"
          >
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-sharp bg-blue/10 text-blue">
              <ShieldCheckIcon width={19} height={19} />
            </span>
            <span className="max-w-[9.5rem] text-[12.5px] font-semibold leading-tight text-navy">
              Safe Electric Registered Contractor
            </span>
          </motion.div>
        </motion.div>
      </div>

      {/* Trust stats row */}
      <div className="relative z-10 border-t border-grey-line bg-base">
        <div className="mx-auto grid max-w-content grid-cols-2 gap-y-6 px-6 py-8 lg:grid-cols-4 lg:gap-0 lg:divide-x lg:divide-grey-line lg:px-16 lg:py-7">
          {STATS.map((s) => (
            <div key={s.label} className="text-center lg:px-6 first:lg:pl-0 last:lg:pr-0">
              <p className="num-tabular text-lg font-semibold text-navy sm:text-xl">
                {s.value}
              </p>
              <p className="mt-1 text-[11.5px] font-medium uppercase tracking-wide text-navy/45">
                {s.label}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
