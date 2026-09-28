import { Section, type Tone } from "@/components/Section";
import { ServiceCell } from "@/components/ServiceCell";
import { T } from "@/components/T";
import { Icon } from "@/components/icons";
import { Heading } from "@/components/parts";
import { cn } from "@/lib/cn";
import { content, ui } from "@/lib/content";

/**
 * Services as one bordered table (labs): every cell shares its hairlines
 * with its neighbours — not separate cards — icon top-left, name and one line under it.
 * Tapping a cell opens the quote form with that service picked.
 */
export default function ServicesIndex({ tone = "base" }: { tone?: Tone }) {
  const items = (content.services?.items || []).filter((s) => s.title).slice(0, 8);
  if (!items.length) return null;
  const lg = items.length % 4 === 0 || items.length > 6 ? 4 : 3;
  // The last cell stretches over any empty columns so the table closes square.
  const spare = (n: number) => (n - (items.length % n)) % n;
  const lastSpan = cn(spare(2) && "col-span-2", lg === 3 ? ["lg:col-span-1", "lg:col-span-2", "lg:col-span-3"][spare(3)] : ["lg:col-span-1", "lg:col-span-2", "lg:col-span-3", "lg:col-span-4"][spare(4)]);
  return (
    <Section slot="services" id="services" tone={tone}>
      <div className="wrap section-y">
        <Heading k="services.heading" intro="services.intro" />
        <p className="mt-6 text-step-small text-muted">{ui("servicesTableHint")}</p>
        <div className={cn("mt-6 grid grid-cols-2 border-l border-t border-line", lg === 4 ? "lg:grid-cols-4" : "lg:grid-cols-3")}>
          {items.map((s, i) => (
            <ServiceCell key={i} service={s.title}
              className={cn("min-h-[9.5rem] border-b border-r border-line p-4 md:min-h-[12rem] md:p-6", i === items.length - 1 && lastSpan)}>
              <Icon name={s.icon} className="h-7 w-7 flex-none text-accent-ink" strokeWidth={1.5} />
              <span className="pt-6 md:pt-8">
                <T k={`services.items.${i}.title`} className="block text-step-1 font-semibold leading-snug text-ink" />
                <T k={`services.items.${i}.text`} className="mt-1.5 hidden text-step-small leading-snug text-muted md:block" />
              </span>
            </ServiceCell>
          ))}
        </div>
      </div>
    </Section>
  );
}
