import { FadeUp, StaggerGrid, StaggerItem } from "./motion/FadeUp";
import {
  HouseIcon,
  PlugIcon,
  BuildingIcon,
  FlameIcon,
  LampIcon,
  AlertIcon,
} from "./icons";

const SERVICES = [
  {
    num: "01",
    icon: HouseIcon,
    title: "Domestic Rewires",
    desc: "Full and partial house rewires, consumer unit upgrades and pre-sale certs across {{TOWN}}.",
  },
  {
    num: "02",
    icon: PlugIcon,
    title: "EV Charger Installation",
    desc: "SEAI-grant-ready home and commercial charger installs, sized and positioned properly.",
  },
  {
    num: "03",
    icon: BuildingIcon,
    title: "Commercial Electrical",
    desc: "Offices, shops and units across {{TOWN}} — fit-outs, upgrades and ongoing maintenance.",
  },
  {
    num: "04",
    icon: FlameIcon,
    title: "Fire Alarm Systems",
    desc: "Design, supply, installation and certification of fire alarm systems to Irish BS standard.",
  },
  {
    num: "05",
    icon: AlertIcon,
    title: "Emergency Callout",
    desc: "Power failure, tripped breakers, fault finding — out to you fast, day or night across {{TOWN}}.",
  },
  {
    num: "06",
    icon: LampIcon,
    title: "Festive Lighting",
    desc: "Professional Christmas and festive lighting installation for homes and businesses across Dublin. Full supply, install and removal service.",
  },
];

export function Services() {
  return (
    <section id="services" className="bg-base px-6 py-24 lg:px-16 lg:py-36">
      <div className="mx-auto max-w-content">
        <FadeUp className="max-w-xl">
          <p className="text-[13px] font-semibold uppercase tracking-wide text-blue">
            What We Do
          </p>
          <h2 className="mt-4 text-balance text-4xl font-semibold tracking-tightest text-navy sm:text-[2.75rem]">
            Every electrical job. Covered.
          </h2>
        </FadeUp>

        <StaggerGrid className="mt-14 grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {SERVICES.map((s) => (
            <StaggerItem key={s.num}>
              <div className="group h-full rounded-sharp border border-grey-line p-7 transition-all duration-300 hover:-translate-y-1 hover:border-blue">
                <div className="flex items-start justify-between">
                  <span className="flex h-11 w-11 items-center justify-center rounded-sharp bg-grey-section text-navy transition-colors duration-300 group-hover:bg-blue group-hover:text-white">
                    <s.icon width={20} height={20} />
                  </span>
                  <span className="num-tabular text-sm font-semibold text-navy/25">
                    {s.num}
                  </span>
                </div>
                <h3 className="mt-6 text-lg font-semibold text-navy">
                  {s.title}
                </h3>
                <p className="mt-2.5 text-[14.5px] leading-relaxed text-navy/60">
                  {s.desc}
                </p>
              </div>
            </StaggerItem>
          ))}
        </StaggerGrid>
      </div>
    </section>
  );
}
