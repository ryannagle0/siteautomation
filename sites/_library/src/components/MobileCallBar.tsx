import { T } from "@/components/T";
import { PhoneIcon, WhatsAppIcon } from "@/components/icons";
import { telHref, ui, waHref } from "@/lib/content";

/**
 * Sticky Call / WhatsApp bar on phones (hidden from md up). WhatsApp only
 * appears when the number is a mobile; with no phone at all the bar
 * becomes a single quote link.
 */
export function MobileCallBar() {
  const bar = "mobileBar";
  return (
    <nav
      aria-label={ui("contactNav")}
      data-tone="base"
      className="fixed inset-x-0 bottom-0 z-40 flex border-t border-line md:hidden"
      style={{
        height: "calc(var(--call-bar-h) + env(safe-area-inset-bottom))",
        paddingBottom: "env(safe-area-inset-bottom)",
        boxShadow: "0 -8px 24px -12px rgb(0 0 0 / 0.35)",
        animation: "bar-in 520ms var(--ease-out) 400ms both",
      }}
    >
      {telHref ? (
        <a href={telHref} className="flex flex-1 items-center justify-center gap-2 bg-accent font-semibold text-accent-fg">
          <PhoneIcon aria-hidden="true" className="h-5 w-5" strokeWidth={2} />
          <T k={`${bar}.call`} fallback={ui("call")} />
        </a>
      ) : (
        <a href="#contact" className="flex flex-1 items-center justify-center gap-2 bg-accent font-semibold text-accent-fg">
          <T k={`${bar}.quote`} fallback={ui("quote")} />
        </a>
      )}
      {waHref && (
        <a href={waHref} target="_blank" rel="noopener"
          className="flex flex-1 items-center justify-center gap-2 bg-surface font-semibold text-ink">
          <WhatsAppIcon aria-hidden="true" className="h-5 w-5" strokeWidth={2} />
          <T k={`${bar}.whatsapp`} fallback={ui("whatsapp")} />
        </a>
      )}
      {telHref && !waHref && (
        <a href="#contact" className="flex flex-1 items-center justify-center gap-2 bg-surface font-semibold text-ink">
          <T k={`${bar}.quote`} fallback={ui("quote")} />
        </a>
      )}
    </nav>
  );
}
