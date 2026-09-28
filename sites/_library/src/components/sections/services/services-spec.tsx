import { Section, type Tone } from "@/components/Section";
import { ServiceCell } from "@/components/ServiceCell";
import { T } from "@/components/T";
import { content, ui } from "@/lib/content";
import { cn } from "@/lib/cn";

/**
 * Spec Sheet template: the scope of work as one ruled table. The first
 * cell carries the brand colour; every cell starts a quote for that line.
 */
export default function ServicesSpec({ tone = "base" }: { tone?: Tone }) {
  const items = (content.services?.items || []).filter((s) => s.title).slice(0, 8);
  if (!items.length) return null;
  const lg = items.length % 3 === 0 && items.length < 7 ? 3 : 4;
  const spare = (n: number) => (n - (items.length % n)) % n;
  const lastSpan = cn(spare(2) && "col-span-2",
    lg === 3 ? ["lg:col-span-1", "lg:col-span-2", "lg:col-span-3"][spare(3)] : ["lg:col-span-1", "lg:col-span-2", "lg:col-span-3", "lg:col-span-4"][spare(4)]);
  return (
    <Section slot="services" id="services" tone={tone}>
      <div className="wrap section-y">
        <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
          <T k="services.heading" as="h2" className="t-headline max-w-xl text-ink" />
          <div className="max-w-sm text-muted">
            <T k="services.intro" as="p" />
            <p className="mt-2 text-step-small">{ui("servicesTableHint")}</p>
          </div>
        </div>
        <div className={cn("mt-10 grid grid-cols-2 border-l-2 border-t-2 border-line", lg === 4 ? "lg:grid-cols-4" : "lg:grid-cols-3")}>
          {items.map((s, i) => (
            <ServiceCell key={i} service={s.title}
              className={cn("min-h-[9rem] justify-end border-b-2 border-r-2 border-line p-4 md:min-h-[12rem] md:p-6",
                i === 0 && "bg-accent text-accent-fg hover:bg-accent-hover", i === items.length - 1 && lastSpan)}>
              <T k={`services.items.${i}.title`}
                className={cn("block text-step-1 font-bold leading-tight", i === 0 ? "text-accent-fg" : "text-ink")} />
              <T k={`services.items.${i}.text`}
                className={cn("mt-1.5 hidden text-step-small leading-snug md:block", i === 0 ? "text-accent-fg" : "text-muted")} />
            </ServiceCell>
          ))}
        </div>
      </div>
    </Section>
  );
}
