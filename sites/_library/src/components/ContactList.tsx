import { ClockIcon, MailIcon, PhoneIcon, PinIcon, WhatsAppIcon } from "@/components/icons";
import { biz, joinTowns, mailHref, phone, telHref, towns, ui, waHref } from "@/lib/content";
import { cn } from "@/lib/cn";

/** Ruled list of every way to reach the business. Rows without data are left out. */
export function ContactList({ className, area = true }: { className?: string; area?: boolean }) {
  const rows = [
    phone && { icon: PhoneIcon, label: ui("phone"), value: phone.display, href: telHref, edit: "business.phone.display" },
    waHref && { icon: WhatsAppIcon, label: ui("whatsapp"), value: phone?.display || "", href: waHref, external: true },
    biz.email && { icon: MailIcon, label: ui("email"), value: biz.email, href: mailHref, edit: "business.email" },
    biz.hours && { icon: ClockIcon, label: ui("hours"), value: biz.hours, edit: "business.hours" },
    area && (towns.length || biz.town) && { icon: PinIcon, label: ui("area"), value: towns.length ? joinTowns(towns, 5) : biz.town || "" },
  ].filter(Boolean) as { icon: typeof PhoneIcon; label: string; value: string; href?: string; edit?: string; external?: boolean }[];
  return (
    <dl className={cn("grid", className)}>
      {rows.map((r, i) => (
        <div key={i} className="grid grid-cols-[auto_1fr] items-start gap-x-4 border-t border-line py-4">
          <r.icon aria-hidden="true" className="mt-0.5 h-5 w-5 text-accent-ink" strokeWidth={1.8} />
          <div className="min-w-0">
            <dt className="t-label text-muted">{r.label}</dt>
            <dd className="mt-1 break-words font-semibold text-ink">
              {r.href ? (
                <a href={r.href} className="no-underline hover:text-accent-ink" {...(r.external ? { target: "_blank", rel: "noopener" } : {})}>
                  <span data-edit={r.edit}>{r.value}</span>
                </a>
              ) : (
                <span data-edit={r.edit}>{r.value}</span>
              )}
            </dd>
          </div>
        </div>
      ))}
    </dl>
  );
}
