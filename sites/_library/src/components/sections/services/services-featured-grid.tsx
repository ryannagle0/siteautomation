import { Img } from "@/components/Img";
import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Icon } from "@/components/icons";
import { Heading } from "@/components/parts";
import { content, hasImage } from "@/lib/content";
import { Check } from "lucide-react";

/** The main service featured large (with its points and photo if any), the rest in a grid below. */
export default function ServicesFeaturedGrid({ tone = "base" }: { tone?: Tone }) {
  const items = (content.services?.items || []).filter((s) => s.title);
  if (!items.length) return null;
  const [lead, ...rest] = items;
  const img = hasImage(lead.image) ? lead.image : null;
  return (
    <Section slot="services" id="services" tone={tone}>
      <div className="wrap section-y">
        <Heading k="services.heading" intro="services.intro" />
        <article className="mt-12 grid gap-8 rounded-theme-lg bg-surface p-6 md:grid-cols-2 md:gap-12 md:p-10">
          <div>
            <Icon name={lead.icon} className="h-9 w-9 text-accent-ink" strokeWidth={1.5} />
            <T k="services.items.0.title" as="h3" className="t-headline mt-5 text-ink" />
            <T k="services.items.0.text" as="p" className="t-lead mt-4" />
          </div>
          {img ? (
            <Img img={img} ratio="4 / 3" sizes="(min-width: 768px) 45vw, 100vw" />
          ) : lead.points?.length ? (
            <ul className="self-end">
              {lead.points.map((p, i) => (
                <li key={i} className="flex items-start gap-3 border-t border-line py-3.5 first:border-t-0">
                  <Check aria-hidden="true" className="mt-0.5 h-5 w-5 flex-none text-accent-ink" strokeWidth={2.2} />
                  <span data-edit={`services.items.0.points.${i}`} className="text-ink">{p}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </article>
        {rest.length > 0 && (
          <dl className="mt-12 border-b border-line">
            {rest.map((_, j) => {
              const i = j + 1;
              return (
                <div key={i} className="grid gap-2 border-t border-line py-5 md:grid-cols-12 md:gap-8">
                  <T k={`services.items.${i}.title`} as="dt" className="t-title text-ink md:col-span-4" />
                  <T k={`services.items.${i}.text`} as="dd" className="text-muted md:col-span-8 md:pt-1" />
                </div>
              );
            })}
          </dl>
        )}
      </div>
    </Section>
  );
}
