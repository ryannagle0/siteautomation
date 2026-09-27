"use client";

import { useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { cn } from "@/lib/cn";

/** Accessible tabs; every panel is server-rendered (hidden when inactive) so the copy stays indexable. */
export function ServiceTabs({ labels, panels }: { labels: ReactNode[]; panels: ReactNode[] }) {
  const [active, setActive] = useState(0);
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  const onKey = (e: KeyboardEvent) => {
    const dir = e.key === "ArrowRight" || e.key === "ArrowDown" ? 1 : e.key === "ArrowLeft" || e.key === "ArrowUp" ? -1 : 0;
    if (!dir) return;
    e.preventDefault();
    const next = (active + dir + labels.length) % labels.length;
    setActive(next);
    refs.current[next]?.focus();
  };
  return (
    <div className="mt-10 grid gap-8 lg:grid-cols-12 lg:gap-14">
      <div role="tablist" aria-orientation="vertical" onKeyDown={onKey}
        className="flex flex-wrap gap-2 lg:col-span-4 lg:flex-col lg:flex-nowrap lg:gap-0">
        {labels.map((label, i) => (
          <button
            key={i}
            ref={(el) => {
              refs.current[i] = el;
            }}
            role="tab"
            id={`svc-tab-${i}`}
            aria-selected={active === i}
            aria-controls={`svc-panel-${i}`}
            tabIndex={active === i ? 0 : -1}
            onClick={() => setActive(i)}
            className={cn(
              "rounded-btn border-theme px-4 py-2.5 text-left font-semibold transition-colors lg:rounded-none lg:border-0 lg:border-t lg:px-0 lg:py-4 lg:text-step-1",
              active === i
                ? "border-accent bg-accent text-accent-fg lg:border-line lg:bg-transparent lg:text-ink"
                : "border-line text-muted hover:text-ink",
            )}
          >
            <span className="lg:flex lg:items-center lg:gap-3">
              <span aria-hidden="true" className={cn("hidden h-2 w-2 flex-none rounded-full lg:inline-block", active === i ? "bg-accent" : "bg-transparent")} />
              {label}
            </span>
          </button>
        ))}
      </div>
      <div className="lg:col-span-8">
        {panels.map((panel, i) => (
          <div key={i} role="tabpanel" id={`svc-panel-${i}`} aria-labelledby={`svc-tab-${i}`} hidden={active !== i}>
            {panel}
          </div>
        ))}
      </div>
    </div>
  );
}
