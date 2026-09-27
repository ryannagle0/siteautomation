import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { PinIcon } from "@/components/icons";
import { content, siteConfig, towns, ui } from "@/lib/content";
import { AreaMap } from "./AreaMap";
import AreaTowns from "./area-towns";

/** A simple map centred on the home town, with the list of towns beside it. Needs lat/lng. */
export default function AreaMapSection({ tone = "surface" }: { tone?: Tone }) {
  const { lat, lng, town } = content.business;
  if (typeof lat !== "number" || typeof lng !== "number") return <AreaTowns tone={tone} />;
  if (!content.area?.heading) return null;
  const list = towns.slice(0, 12);
  return (
    <Section slot="service-area" id="area" tone={tone}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:items-center lg:gap-14">
        <div className="lg:col-span-5">
          <T k="area.heading" as="h2" className="t-headline text-ink" />
          <T k="area.intro" as="p" className="t-lead mt-4" />
          {list.length > 0 && (
            <ul className="mt-8 grid grid-cols-2 gap-x-6">
              {list.map((t, i) => (
                <li key={i} className="flex items-center gap-2.5 border-t border-line py-3">
                  <PinIcon aria-hidden="true" className="h-4 w-4 flex-none text-accent-ink" strokeWidth={2} />
                  <span data-edit={`area.towns.${i}`} className="font-medium text-ink">{t}</span>
                </li>
              ))}
            </ul>
          )}
          <T k="area.note" as="p" className="mt-6 text-muted" />
        </div>
        <div role="img" aria-label={ui("mapLabel", { town: town || "" })}
          className="relative h-[320px] overflow-hidden rounded-theme-lg border-theme border-line bg-surface-2 md:h-[440px] lg:col-span-7">
          <AreaMap lng={lng} lat={lat} dark={siteConfig.preset === "industrial"} />
        </div>
      </div>
    </Section>
  );
}
