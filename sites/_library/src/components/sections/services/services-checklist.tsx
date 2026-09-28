import { Section, type Tone } from "@/components/Section";
import { ServiceCell } from "@/components/ServiceCell";
import { T } from "@/components/T";
import { content, ui } from "@/lib/content";

/**
 * Van Livery template: what they do as a plain two-column checklist with
 * hi-vis markers, like the list painted under the name on a van. Each line
 * starts a quote for that service.
 */
export default function ServicesChecklist({ tone = "base" }: { tone?: Tone }) {
  const items = (content.services?.items || []).filter((s) => s.title).slice(0, 10);
  if (!items.length) return null;
  return (
    <Section slot="services" id="services" tone={tone}>
      <div className="wrap section-y grid gap-10 lg:grid-cols-12 lg:gap-14">
        <div className="lg:col-span-4">
          <T k="services.heading" as="h2" className="t-headline text-accent-ink" />
          <T k="services.intro" as="p" className="mt-5 max-w-md text-muted" />
          <p className="mt-5 text-step-small text-muted">{ui("servicesTableHint")}</p>
        </div>
        <ul className="grid content-start gap-x-10 sm:grid-cols-2 lg:col-span-8">
          {items.map((s, i) => (
            <li key={i} className="border-b-2 border-line">
              <ServiceCell service={s.title} className="w-full flex-row items-center gap-4 py-4 hover:bg-transparent">
                <span aria-hidden="true" className="h-3.5 w-3.5 flex-none border-2 border-ink bg-[var(--livery)]" />
                <span className="flex flex-col">
                  <T k={`services.items.${i}.title`} className="text-step-1 font-semibold leading-snug text-ink" />
                  <T k={`services.items.${i}.text`} className="mt-0.5 text-step-small leading-snug text-muted" />
                </span>
              </ServiceCell>
            </li>
          ))}
        </ul>
      </div>
    </Section>
  );
}
