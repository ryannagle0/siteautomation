import { Star } from "lucide-react";
import { T } from "@/components/T";
import { PhoneIcon, PinIcon, WhatsAppIcon } from "@/components/icons";
import { content, phone, primaryHref, telHref, towns, ui, waHref } from "@/lib/content";
import { cn } from "@/lib/cn";

/** Star rating in accent ink; half-stars round to the nearest whole. */
export function Stars({ value = 5, className }: { value?: number; className?: string }) {
  const full = Math.round(Math.max(0, Math.min(5, value)));
  return (
    <span className={cn("inline-flex items-center gap-0.5 text-accent-ink", className)} role="img" aria-label={ui("starsLabel", { value })}>
      {Array.from({ length: 5 }, (_, i) => (
        <Star key={i} aria-hidden="true" className="h-[1em] w-[1em]" strokeWidth={1.5}
          fill={i < full ? "currentColor" : "none"} />
      ))}
    </span>
  );
}

/** The signature coverage line: pin + the towns this business works in. */
export function Coverage({ className, max = 5, lead }: { className?: string; max?: number; lead?: string }) {
  const list = towns.slice(0, max);
  const home = content.business.town;
  if (!list.length && !home) return null;
  const items = list.length ? list : [home as string];
  return (
    <p className={cn("flex items-start gap-2 text-muted", className)}>
      <PinIcon aria-hidden="true" className="mt-[0.2em] h-[1.1em] w-[1.1em] flex-none text-accent-ink" strokeWidth={1.8} />
      <span className="flex min-w-0 flex-wrap gap-x-1.5">
        {lead && <span className="text-ink">{lead}</span>}
        {items.map((town, i) => (
          <span key={i} className="whitespace-nowrap">
            <span data-edit={list.length ? `area.towns.${i}` : "business.town"}>{town}</span>
            {(i < items.length - 1 || towns.length > max) && <span aria-hidden="true" className="pl-1.5 opacity-50">·</span>}
          </span>
        ))}
        {towns.length > max && <span className="opacity-70">{ui("more")}</span>}
      </span>
    </p>
  );
}

/** The phone number set as display type. Renders nothing without a phone. */
export function PhoneBig({ className }: { className?: string }) {
  if (!phone) return null;
  return (
    <a href={telHref} aria-label={ui("callNumber", { phone: phone.display })} className={cn("group inline-flex flex-col no-underline", className)}>
      <span data-edit="business.phone.display" className="t-phone text-step-4 text-ink transition-colors group-hover:text-accent-ink">
        {phone.display}
      </span>
    </a>
  );
}

/**
 * Primary + secondary actions for a slot. Primary calls (or jumps to the
 * contact form when there's no phone); secondary goes to the quote form, or
 * WhatsApp when `whatsapp` is set and the number is a mobile.
 */
export function Actions({
  slot,
  className,
  size = "lg",
  whatsapp = false,
}: {
  slot: "hero" | "cta";
  className?: string;
  size?: "md" | "lg";
  whatsapp?: boolean;
}) {
  const primaryKey = slot === "hero" ? "hero.primaryCta" : "cta.primary";
  const secondaryKey = slot === "hero" ? "hero.secondaryCta" : "cta.secondary";
  const secondaryHref = whatsapp && waHref ? waHref : "#contact";
  return (
    <div className={cn("flex flex-col gap-3 sm:flex-row sm:flex-wrap", className)}>
      <a href={primaryHref} className={cn("btn btn-primary", size === "lg" && "btn-lg")}>
        {telHref && <PhoneIcon aria-hidden="true" strokeWidth={2} />}
        <T k={primaryKey} fallback={telHref ? ui("callNumber", { phone: phone?.display || "" }) : ui("quote")} />
      </a>
      <a href={secondaryHref} className={cn("btn btn-secondary", size === "lg" && "btn-lg")}
        {...(secondaryHref.startsWith("http") ? { target: "_blank", rel: "noopener" } : {})}>
        {whatsapp && waHref && <WhatsAppIcon aria-hidden="true" strokeWidth={2} />}
        <T k={secondaryKey} fallback={whatsapp && waHref ? ui("whatsapp") : ui("quote")} />
      </a>
    </div>
  );
}

/** Section heading + optional intro, shared rhythm for every section. */
export function Heading({
  k,
  intro,
  className,
  align = "left",
  as = "h2",
}: {
  k: string;
  intro?: string;
  className?: string;
  align?: "left" | "center";
  as?: "h1" | "h2";
}) {
  return (
    <div className={cn("max-w-3xl", align === "center" && "mx-auto text-center", className)}>
      <T k={k} as={as} className="t-headline text-ink" />
      {intro && <T k={intro} as="p" className={cn("t-lead mt-4 max-w-2xl", align === "center" && "mx-auto")} />}
    </div>
  );
}
