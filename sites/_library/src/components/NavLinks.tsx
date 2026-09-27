import { content } from "@/lib/content";
import { cn } from "@/lib/cn";

/** Desktop nav links (md and up). */
export function NavLinks({ className, linkClassName }: { className?: string; linkClassName?: string }) {
  const links = content.nav?.links || [];
  if (!links.length) return null;
  return (
    <ul className={cn("hidden items-center gap-7 md:flex", className)}>
      {links.map((l, i) => (
        <li key={i}>
          <a href={l.href} data-edit={`nav.links.${i}.label`}
            className={cn("text-step-small font-medium text-muted no-underline transition-colors hover:text-ink", linkClassName)}>
            {l.label}
          </a>
        </li>
      ))}
    </ul>
  );
}
