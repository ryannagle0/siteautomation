import { Img } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Icon } from "@/components/icons";
import { Heading } from "@/components/parts";
import { content, hasImage, primaryHref, telHref, ui } from "@/lib/content";
import { Check } from "lucide-react";
import { ServiceTabs } from "./ServiceTabs";

/** One service at a time: names as tabs (a scrolling row on phones), detail panel beside. */
export default function ServicesTabs({ tone = "base" }: { tone?: Tone }) {
  const items = (content.services?.items || []).filter((s) => s.title);
  if (!items.length) return null;
  const labels = items.map((s, i) => <span key={i} data-edit={`services.items.${i}.title`}>{s.title}</span>);
  const panels = items.map((s, i) => (
    <div key={i} className="grid gap-8 md:grid-cols-[1fr_auto] md:items-start">
      <div>
        <Icon name={s.icon} className="h-10 w-10 text-accent-ink" strokeWidth={1.4} />
        <h3 className="t-headline mt-5 text-ink">{s.title}</h3>
        <T k={`services.items.${i}.text`} as="p" className="t-lead mt-4 max-w-xl" />
        {s.points?.length ? (
          <ul className="mt-6 max-w-xl">
            {s.points.map((p, j) => (
              <li key={j} className="flex items-start gap-3 border-t border-line py-3 first:border-t-0">
                <Check aria-hidden="true" className="mt-0.5 h-5 w-5 flex-none text-accent-ink" strokeWidth={2.2} />
                <span data-edit={`services.items.${i}.points.${j}`}>{p}</span>
              </li>
            ))}
          </ul>
        ) : null}
        <a href={primaryHref} className="btn btn-primary mt-8">
          {telHref ? ui("askAbout") : ui("quote")}
        </a>
      </div>
      {hasImage(s.image) && <Img img={s.image} ratio="4 / 5" className="w-full md:w-72" sizes="(min-width: 768px) 18rem, 100vw" />}
    </div>
  ));
  return (
    <Section slot="services" id="services" tone={tone}>
      <div className="wrap section-y">
        <Heading k="services.heading" intro="services.intro" />
        <ServiceTabs labels={labels} panels={panels} />
      </div>
    </Section>
  );
}
