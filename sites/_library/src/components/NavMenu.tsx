"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Menu, X } from "lucide-react";
import type { Link } from "@/lib/content";
import { cn } from "@/lib/cn";

/** Phone-width disclosure menu for the nav links. Closes on link tap / Escape. */
export function NavMenu({
  links,
  className,
  openLabel,
  closeLabel,
}: {
  links: Link[];
  className?: string;
  openLabel: string;
  closeLabel: string;
}) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    const onClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("click", onClick);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("click", onClick);
    };
  }, [open]);

  if (!links.length) return null;
  return (
    <div ref={ref} className={cn("md:hidden", className)}>
      <button
        type="button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen((v) => !v)}
        className="-mr-2 inline-flex h-11 w-11 items-center justify-center rounded-btn text-ink"
      >
        {open ? <X aria-hidden="true" className="h-6 w-6" /> : <Menu aria-hidden="true" className="h-6 w-6" />}
        <span className="sr-only">{open ? closeLabel : openLabel}</span>
      </button>
      <div
        id={id}
        hidden={!open}
        className="absolute inset-x-0 top-full border-b border-line bg-bg shadow-[0_16px_24px_-16px_rgb(0_0_0/0.3)]"
      >
        <ul className="wrap flex flex-col py-2">
          {links.map((l, i) => (
            <li key={i} className="border-t border-line first:border-t-0">
              <a href={l.href} onClick={() => setOpen(false)} data-edit={`nav.links.${i}.label`}
                className="flex min-h-12 items-center text-step-1 font-medium text-ink no-underline">
                {l.label}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
