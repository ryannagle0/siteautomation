import { Section, type Tone } from "@/components/Section";
import { T } from "@/components/T";
import { Icon } from "@/components/icons";
import { content, primaryHref, telHref, ui } from "@/lib/content";

/** Heading held on the left (sticky on desktop), services as a ruled list on the right. */
export default function ServicesListIcons({ tone = "base" }: { tone?: Tone }) {
  const items = (content.services?.items || []).filter((s) => s.title);
  if (!items.length) return null;
  return (
    <Section slot="services" id="services" tone={tone}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-5">
          <div className="lg:sticky lg:top-28">
            <T k="services.heading" as="h2" className="t-headline text-ink" />
            <T k="services.intro" as="p" className="t-lead mt-4" />
            <a href={primaryHref} className="link mt-6 inline-block">
              {telHref ? ui("notSure") : ui("notSureNoPhone")}
            </a>
          </div>
        </div>
        <ul className="lg:col-span-7">
          {items.map((s, i) => (
            <li key={i} className="grid grid-cols-[auto_1fr] gap-x-5 border-t border-line py-7 first:border-t-0 first:pt-0 lg:first:pt-1">
              <span className="flex h-12 w-12 items-center justify-center rounded-theme bg-accent-soft">
                <Icon name={s.icon} className="h-6 w-6 text-accent-ink" />
              </span>
              <div>
                <T k={`services.items.${i}.title`} as="h3" className="t-title text-ink" />
                <T k={`services.items.${i}.text`} as="p" className="mt-2 text-muted" />
              </div>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
